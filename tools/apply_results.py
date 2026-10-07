#!/usr/bin/env python3
"""Add a tour's results from the BDT Scorer (scorer.html) to the Master Playbook.

    python3 tools/apply_results.py results.txt "Big Dogs Tour - Master Playbook.xlsx" [-o out.xlsx]

results.txt is the message the scorer sent (the summary plus the "BDT DATA" block).
Rows are written into the first empty rows of the input sheets: Tours, Players,
RC Matches, Individual, Trophies and Team Sheets. Every other sheet recalculates
from those when the workbook is next opened (it is set to recalculate on load).

The workbook is edited at the XML level, cell by cell, so its formatting, formulas,
drop-down lists and hidden sheets are left exactly as they were. It refuses to run
if the year already has Ryder Cup or Individual rows, so nothing is entered twice.
"""
import argparse, datetime, json, os, re, shutil, sys, zipfile
from lxml import etree

NS = 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'
RNS = 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'
Q = lambda t: '{%s}%s' % (NS, t)
TEAM = {'BH': 'Bloodhounds', 'RT': 'Retrievers'}
RESULT = {'BH': 'Bloodhounds', 'RT': 'Retrievers', 'H': 'Halved'}


def col_num(letters):
    n = 0
    for ch in letters:
        n = n * 26 + ord(ch) - 64
    return n


def split_ref(ref):
    m = re.match(r'([A-Z]+)(\d+)$', ref)
    return m.group(1), int(m.group(2))


def excel_date(iso):
    d = datetime.date.fromisoformat(iso)
    return (d - datetime.date(1899, 12, 30)).days


class Sheet:
    def __init__(self, name, path, xml):
        self.name, self.path = name, path
        self.root = etree.fromstring(xml)
        self.data = self.root.find(Q('sheetData'))
        self.rows = {int(r.get('r')): r for r in self.data.findall(Q('row'))}

    def has_value(self, row, col):
        r = self.rows.get(row)
        if r is None:
            return False
        for c in r.findall(Q('c')):
            if c.get('r') == f'{col}{row}':
                return c.find(Q('v')) is not None or c.find(Q('is')) is not None or c.find(Q('f')) is not None
        return False

    def column_values(self, col, shared):
        out = []
        for n, r in self.rows.items():
            for c in r.findall(Q('c')):
                if c.get('r') == f'{col}{n}':
                    out.append(cell_text(c, shared))
        return out

    def find_row(self, col, value, shared):
        """Row number whose cell in col holds value (e.g. the year), or None."""
        for n in sorted(self.rows):
            for c in self.rows[n].findall(Q('c')):
                if c.get('r') == f'{col}{n}' and cell_text(c, shared).strip() in (str(value), f'{value}.0'):
                    return n
        return None

    def next_empty(self, col='A', start=2):
        n = start
        while self.has_value(n, col):
            n += 1
        return n

    def set(self, ref, value):
        if value is None or value == '':
            return
        letters, n = split_ref(ref)
        row = self.rows.get(n)
        if row is None:
            row = etree.Element(Q('row'))
            row.set('r', str(n))
            later = [k for k in self.rows if k > n]
            if later:
                self.rows[min(later)].addprevious(row)
            else:
                self.data.append(row)
            self.rows[n] = row
        cell = None
        for c in row.findall(Q('c')):
            if c.get('r') == ref:
                cell = c
                break
        if cell is None:
            cell = etree.Element(Q('c'))
            cell.set('r', ref)
            after = [c for c in row.findall(Q('c')) if col_num(split_ref(c.get('r'))[0]) > col_num(letters)]
            if after:
                after[0].addprevious(cell)
            else:
                row.append(cell)
            # new cells take the formatting (e.g. date format) of the nearest cell above in the same column
            for k in range(n - 1, 1, -1):
                above = self.rows.get(k)
                st = None
                if above is not None:
                    st = next((c.get('s') for c in above.findall(Q('c')) if c.get('r') == f'{letters}{k}'), None)
                if st:
                    cell.set('s', st)
                    break
        if cell.find(Q('f')) is not None:
            raise SystemExit(f'{self.name}!{ref} holds a formula - not overwriting it')
        for ch in list(cell):
            cell.remove(ch)
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            cell.attrib.pop('t', None)
            v = etree.SubElement(cell, Q('v'))
            v.text = repr(value) if isinstance(value, float) else str(value)
        else:
            cell.set('t', 'inlineStr')
            is_ = etree.SubElement(cell, Q('is'))
            t = etree.SubElement(is_, Q('t'))
            t.text = str(value)
            if t.text != t.text.strip():
                t.set('{http://www.w3.org/XML/1998/namespace}space', 'preserve')

    def xml(self):
        return etree.tostring(self.root, xml_declaration=True, encoding='UTF-8', standalone=True)


def cell_text(c, shared):
    v = c.find(Q('v'))
    if c.get('t') == 's' and v is not None:
        return shared[int(v.text)]
    if c.get('t') == 'inlineStr':
        return ''.join(c.find(Q('is')).itertext())
    return v.text if v is not None else ''


def read_packet(path):
    text = open(path, encoding='utf-8').read()
    m = re.search(r'--- BDT DATA[^\n]*\n(.*?)\n--- END ---', text, re.S)
    return json.loads(m.group(1) if m else text)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('results')
    ap.add_argument('playbook')
    ap.add_argument('-o', '--out')
    ap.add_argument('--site', default=os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                    help='website folder: the tour country, round days and full course names are saved in <year>.json there')
    a = ap.parse_args()
    D = read_packet(a.results)
    out = a.out or a.playbook.replace('.xlsx', f' (with {D["year"]}).xlsx')
    Y = D['year']

    z = zipfile.ZipFile(a.playbook)
    wb = etree.fromstring(z.read('xl/workbook.xml'))
    rels = etree.fromstring(z.read('xl/_rels/workbook.xml.rels'))
    target = {r.get('Id'): r.get('Target') for r in rels}
    paths = {}
    for s in wb.find(Q('sheets')):
        t = target[s.get('{%s}id' % RNS)]
        paths[s.get('name')] = 'xl/' + t.lstrip('/').replace('xl/', '', 1) if not t.startswith('xl/') else t
    sst = etree.fromstring(z.read('xl/sharedStrings.xml'))
    shared = [''.join(si.itertext()) for si in sst.findall(Q('si'))]
    sheets = {n: Sheet(n, paths[n], z.read(paths[n])) for n in
              ['Tours', 'Players', 'RC Matches', 'Individual', 'Trophies', 'Team Sheets', 'Tour Shirts', 'Handicaps']}

    for n in ('RC Matches', 'Individual'):
        if str(Y) in sheets[n].column_values('A', shared):
            raise SystemExit(f'{n} already has rows for {Y} - nothing changed.')

    squad = {t: [p for p, tm in D['team'].items() if tm == t] for t in ('BH', 'RT')}
    played = [R for R in D['rounds'] if not R.get('rainedOff')]
    log = []

    # Tours (one row for the year; updated in place if the year is already listed)
    T = sheets['Tours']
    tour = D.get('tour', {})
    r = T.find_row('A', Y, shared) or T.next_empty()
    vals = {'A': Y, 'B': tour.get('location'), 'C': len(played), 'D': 'Yes',
            'E': D['rounds'][0]['course'], 'F': D['rounds'][1]['course'], 'G': D['rounds'][2]['course'],
            'H': len(squad['BH']) + len(squad['RT']), 'I': D['cap'].get('BH'), 'J': D['cap'].get('RT'),
            'M': tour.get('accommodation'),
            'P': excel_date(tour['start']) if tour.get('start') else None,
            'S': excel_date(tour['end']) if tour.get('end') else None}
    for col, v in vals.items():
        if not T.has_value(r, col):   # keep anything already typed in for the year
            T.set(f'{col}{r}', v)
    log.append(f'Tours: row {r}')

    # Players (first-timers only)
    P = sheets['Players']
    known = set(P.column_values('A', shared))
    for np in D.get('newPlayers', []):
        if np.get('short') and np['short'] not in known:
            r = P.next_empty()
            P.set(f'A{r}', np['short']); P.set(f'C{r}', np.get('real')); P.set(f'P{r}', np.get('real'))
            log.append(f'Players: added {np["short"]} at row {r}')

    # Team Sheets
    S = sheets['Team Sheets']
    for t in ('BH', 'RT'):
        for i, p in enumerate(squad[t], 1):
            r = S.next_empty()
            S.set(f'A{r}', Y); S.set(f'B{r}', TEAM[t]); S.set(f'C{r}', i); S.set(f'D{r}', p)
            if D['cap'].get(t) == p:
                S.set(f'E{r}', 'Y')
    log.append(f'Team Sheets: {len(squad["BH"]) + len(squad["RT"])} rows')

    # Tour Shirts
    SH = sheets['Tour Shirts']
    for t in ('BH', 'RT'):
        h = (D.get('shirts') or {}).get(t) or {}
        if h.get('colour'):
            r = SH.next_empty()
            SH.set(f'A{r}', Y); SH.set(f'B{r}', TEAM[t]); SH.set(f'C{r}', h['colour'])
            SH.set(f'D{r}', h.get('logo')); SH.set(f'E{r}', 'The ' + TEAM[t])
            log.append(f'Tour Shirts: {TEAM[t]} at row {r}')

    # RC Matches
    M = sheets['RC Matches']
    nm = 0
    for R in played:
        for m in R['matches']:
            r = M.next_empty()
            bh = [x for x in m['bh'] if x] + ['', '']
            rt = [x for x in m['rt'] if x] + ['', '']
            v = m.get('value', 1)
            # a solo player's two half-point singles on a fourball day are recorded as singles
            solo = R['fmt'] == 'Fourball' and len([x for x in m['bh'] if x]) == 1 and len([x for x in m['rt'] if x]) == 1
            M.set(f'A{r}', Y); M.set(f'B{r}', R['r']); M.set(f'C{r}', 'Singles' if solo else R['fmt'])
            M.set(f'D{r}', 0.5 if float(v) == 0.5 else 1)
            M.set(f'E{r}', bh[0]); M.set(f'F{r}', bh[1]); M.set(f'G{r}', rt[0]); M.set(f'H{r}', rt[1])
            M.set(f'I{r}', RESULT.get(m['res'], '')); M.set(f'J{r}', m.get('margin') or ('A/S' if m['res'] == 'H' else ''))
            M.set(f'K{r}', 'Played')
            M.set(f'L{r}', m.get('note') or ('Solo player - two half-point singles on a fourball day' if solo and float(v) == 0.5 else None))
            nm += 1
    log.append(f'RC Matches: {nm} matches')

    # Individual
    I = sheets['Individual']
    final = D.get('final', {})
    rained = [R['r'] for R in D['rounds'] if R.get('rainedOff')]
    pos = lambda p: final.get(p) or D.get('positions', {}).get(p)
    # in finishing order, ties by name, as the Playbook keeps them (records lists show ties in this order)
    for p in sorted(squad['BH'] + squad['RT'], key=lambda p: (pos(p) if isinstance(pos(p), (int, float)) else 999, p)):  # ties: by name
        r = I.next_empty()
        I.set(f'A{r}', Y); I.set(f'B{r}', p)
        for R, col in zip(D['rounds'], 'CDE'):
            if not R.get('rainedOff') and p in R['scores']:
                I.set(f'{col}{r}', R['scores'][p])
        I.set(f'F{r}', final.get(p) or D.get('positions', {}).get(p))
        if rained:
            I.set(f'G{r}', 'Round ' + ' & '.join('I' * x for x in rained) + ' rained off')
    log.append(f'Individual: {len(squad["BH"]) + len(squad["RT"])} players')

    # Handicaps (one row per Players row, three rows lower; a column per year)
    H = sheets['Handicaps']
    hrow = H.rows.get(4)
    ycol = None
    for c in (hrow.findall(Q('c')) if hrow is not None else []):
        if re.match(rf'{Y}\b', cell_text(c, shared) or ''):
            ycol = split_ref(c.get('r'))[0]
    prow = {}
    for n in sorted(P.rows):
        for c in P.rows[n].findall(Q('c')):
            if c.get('r') == f'A{n}':
                prow[cell_text(c, shared)] = n
    nh = 0
    for p, h in (D.get('hcp') or {}).items():
        if ycol and p in prow and h is not None:
            H.set(f'{ycol}{prow[p] + 3}', h)
            nh += 1
    # everyone else keeps last year's handicap (change it by hand if theirs moved)
    nc = 0
    if ycol:
        prev = None
        for c in hrow.findall(Q('c')):
            if split_ref(c.get('r'))[0] == ycol:
                break
            prev = split_ref(c.get('r'))[0]
        for n in sorted(H.rows):
            if n <= 4 or H.has_value(n, ycol) or not prev:
                continue
            pc = next((c for c in H.rows[n].findall(Q('c')) if c.get('r') == f'{prev}{n}'), None)
            v = pc.find(Q('v')) if pc is not None and pc.get('t') in (None, 'n') else None
            if v is not None and v.text not in (None, ''):
                H.set(f'{ycol}{n}', int(float(v.text)) if float(v.text).is_integer() else float(v.text))
                nc += 1
    log.append(f'Handicaps: {nh} entered, {nc} carried over from last year' if ycol
               else f'Handicaps: no {Y} column found - type them in by hand')

    # Trophies
    TR = sheets['Trophies']
    nt = 0
    ORDER = ['Big Dog', '2nd', '3rd', 'Shitzu', 'Great Dane', 'St Bernard', 'Elton Ravo Prize', 'Xolo', 'Rottweiler',
             'Poodle', 'Cheat', 'Seve & Olly', 'Goblat', 'Duncan Goodhew']
    for t in sorted(D['trophies'], key=lambda t: ORDER.index(t['t']) if t['t'] in ORDER else 99):
        for w in [w for w in t['w'] if w]:
            r = TR.next_empty()
            TR.set(f'A{r}', Y); TR.set(f'B{r}', t['t']); TR.set(f'C{r}', w); TR.set(f'D{r}', t.get('why'))
            nt += 1
    log.append(f'Trophies: {nt} rows')

    # write a new copy of the workbook, every other part byte for byte
    shutil.copyfile(a.playbook, out)
    changed = {s.path: s.xml() for s in sheets.values()}
    with zipfile.ZipFile(a.playbook) as src, zipfile.ZipFile(out, 'w', zipfile.ZIP_DEFLATED) as dst:
        for item in src.infolist():
            data = changed.get(item.filename, src.read(item.filename))
            dst.writestr(item, data)
    # website extras the Playbook has no place for (used by tools/build_site.py for a new tour)
    if a.site and os.path.isdir(a.site):
        f = os.path.join(a.site, f'{Y}.json')
        M = json.load(open(f, encoding='utf-8')) if os.path.exists(f) else {}
        if not M:
            sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
            from build_site import blank_media
            M = blank_media(Y)
        M.update({k: v for k, v in (('country', tour.get('country')), ('round_days', tour.get('days')),
                                     ('course_names', tour.get('courses'))) if v})
        json.dump(M, open(f, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
        log.append(f'Website: saved country, round days and course names in {os.path.basename(f)}')

    print('\n'.join(log))
    print('Written', out)


if __name__ == '__main__':
    main()
