import re
"""Interesting Fact generator for the tour pages.

Each fact type looks at the whole playbook history and returns a fact for one year (or None if that
type has nothing notable to say).  build_tour_page.py picks one:
  * tour_media/<year>.json  "fact": {"title":..., "text":...}   -> used as-is (hand-written override)
  * tour_media/<year>.json  "fact_type": "comeback"              -> force a type
  * otherwise types are tried in a year-rotated order so neighbouring tours get different kinds of fact.
"""
from collections import defaultdict

TEAM = {'BH': 'Bloodhounds', 'RT': 'Retrievers'}


def half(v):
    v = float(v)
    w = int(v)
    f = round(v - w, 2)
    if f == 0.5:
        return (str(w) if w else '') + '½'
    if f in (0.25, 0.75):
        return f'{v:g}'
    return str(w)


def poss(n):
    return n + ("'" if n.endswith('s') else "'s")


def ordn(n):
    return f'{n}{"th" if 10 <= n % 100 <= 20 else {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")}'


def team_results():
    import csv, os
    here = os.path.dirname(os.path.abspath(__file__))
    for d in (os.environ.get('BDT_SRC', ''), os.path.dirname(here), '/mnt/user-data/uploads/Claude Workings For New Webpages'):
        f = os.path.join(d, 'bdt_team_results.csv')
        if d and os.path.exists(f):
            with open(f, encoding='utf-8-sig') as fh:
                return {int(r['year']): {'Bloodhounds': 'BH', 'Retrievers': 'RT', 'Halved': 'H'}.get(r['result'].strip())
                        for r in csv.DictReader(fh)}
    return {}


def load(wb):
    """Collect per-year history from the workbook."""
    rc = defaultdict(lambda: defaultdict(lambda: [0.0, 0.0]))
    for r in list(wb['RC Matches'].iter_rows(values_only=True))[1:]:
        if not r[0] or r[10] == 'Abandoned':
            continue
        rc[r[0]][r[1]][0] += float(r[15] or 0)
        rc[r[0]][r[1]][1] += float(r[16] or 0)
    ind = defaultdict(list)
    for r in list(wb['Individual'].iter_rows(values_only=True))[1:]:
        if r[0] and r[1]:
            ind[r[0]].append({'p': r[1], 'r': [x for x in r[2:5]], 'tot': r[7], 'pos': r[5]})
    sheets = defaultdict(list)
    for r in list(wb['Team Sheets'].iter_rows(values_only=True))[1:]:
        if r[0] and r[3]:
            sheets[r[0]].append(r[3])
    th, *tours = list(wb['Tours'].iter_rows(values_only=True))
    ov_col = next(k for k, h in enumerate(th) if h and str(h).lower().startswith('winner override'))
    override = {t[0]: t[ov_col] for t in tours if t[0]}
    res = {}
    for y, rounds in rc.items():
        bh = sum(v[0] for v in rounds.values()); rt = sum(v[1] for v in rounds.values())
        w = 'BH' if bh > rt else 'RT' if rt > bh else 'H'
        if override.get(y):
            o = str(override[y]).lower()
            w = 'BH' if 'blood' in o else 'RT' if 'retr' in o else 'H' if 'halv' in o else w
        res[y] = {'bh': bh, 'rt': rt, 'w': w, 'r1': rounds.get(1, [0, 0])}
    # the team-results file (also used by the Tours page) is the final word on each cup's result,
    # e.g. 2012 was abandoned after Round II and later settled 6-6 off-tour, so it counts as halved
    for y, r in team_results().items():
        if y in res and r:
            res[y]['w'] = r
    # everyone known to have been on a tour before full records began: 2002/2003 attendee lists in the
    # Tours notes, plus trophy winners (the Elton Ravo Prize is for an off-tour song, so it doesn't count)
    early = defaultdict(set)
    notes_col = next((k for k, h in enumerate(th) if h and str(h).lower().startswith('notes')), None)
    for t in tours:
        if t[0] and notes_col is not None and t[notes_col]:
            m = re.search(r'Attendees \(\d+\):\s*([^|]+)', str(t[notes_col]))
            if m:
                early[t[0]] |= {re.sub(r'\s*\(.*$', '', p).strip().rstrip('. ').strip() for p in re.sub(r'\([^)]*\)?', '', m.group(1)).split(',') if re.sub(r'\s*\(.*$', '', p).strip().rstrip('. ').strip()}
    for r in list(wb['Trophies'].iter_rows(values_only=True))[1:]:
        if r[0] and r[2] and 'ravo' not in str(r[1]).lower():
            early[r[0]] |= {p.strip() for p in str(r[2]).split('/') if p.strip()}
    # single-round scores known from before full records began (e.g. Paddy's 48 and Robbo's 9 at La Manga in
    # 2003) are kept as 'manual' rows at the foot of the hidden calc_Rounds sheet - include them in round records
    extra = []
    if 'calc_Rounds' in wb.sheetnames:
        for r in wb['calc_Rounds'].iter_rows(min_row=2, values_only=True):
            if r and str(r[0]).strip().lower() == 'manual' and isinstance(r[4], (int, float)) and r[3]:
                extra.append({'y': int(r[3]), 'p': r[2], 'r': int(r[1] or 0), 's': r[4]})
    return {'rc': rc, 'res': res, 'ind': ind, 'sheets': sheets, 'early': early, 'extra': extra}


# ---------------------------------------------------------------- fact types
def f_comeback(H, Y, names):
    """A team behind after Round I that came back."""
    R = H['res']
    if Y not in R:
        return None
    r1 = R[Y]['r1']; d = r1[0] - r1[1]
    if abs(d) < 1.5:
        return None
    trail = 'BH' if d < 0 else 'RT'
    fin = R[Y]['bh'] - R[Y]['rt']
    out = 'won' if (fin > 0 and trail == 'BH') or (fin < 0 and trail == 'RT') else 'halved' if fin == 0 else None
    if not out:
        return None
    # how rare: other years where the side trailing by >= this much after R1 avoided defeat
    same = [y for y, v in R.items() if y != Y and abs(v['r1'][0] - v['r1'][1]) >= abs(d) and
            ((v['r1'][0] < v['r1'][1] and v['bh'] >= v['rt']) or (v['r1'][1] < v['r1'][0] and v['rt'] >= v['bh']))]
    rest = [R[Y]['bh'] - r1[0], R[Y]['rt'] - r1[1]]
    k = 0 if trail == 'BH' else 1
    lead = f"The {TEAM[trail]} were {half(abs(d))} points down after Round I ({half(r1[0])}–{half(r1[1])})"
    tail = (f" but took Rounds II and III {half(rest[k])}–{half(rest[1 - k])} to "
            + ('win the cup' if out == 'won' else 'halve the cup') + '.')
    rare = (" No other team has come back from that far behind after day one without losing."
            if not same else f" The only other side to avoid defeat from that far back after day one: {', '.join(map(str, same))}.")
    return {'type': 'comeback', 'title': 'The great comeback', 'text': lead + tail + rare}


def f_streak(H, Y, names):
    """Back-to-back / run of the same Ryder Cup result."""
    R = H['res']
    if Y not in R:
        return None
    ys = sorted(R)
    w = R[Y]['w']; n = 1; y = Y
    while ys.index(y) > 0 and R[ys[ys.index(y) - 1]]['w'] == w:
        y = ys[ys.index(y) - 1]; n += 1
    if n < 2:
        return None
    first = Y - n + 1
    if w == 'H':
        prev_best = 0; run = 0
        for yy in ys:
            if yy >= first:
                break
            run = run + 1 if R[yy]['w'] == 'H' else 0
            prev_best = max(prev_best, run)
        return {'type': 'streak', 'title': 'Honours even, again',
                'text': f"{n} halved Ryder Cups in a row ({first}–{Y})."
                        + (" The first time the cup has been shared in consecutive years." if prev_best < n else '')}
    best = 0; run = 0
    for yy in ys:
        if yy >= first:
            break
        run = run + 1 if R[yy]['w'] == w else 0
        best = max(best, run)
    tail = (" Their longest winning run ever." if n > best else " Equalling their longest winning run." if n == best
            else f" Their record is {best} in a row.")
    return {'type': 'streak', 'title': f'{n} in a row',
            'text': f"The {TEAM[w]}' {ordn(n)} Ryder Cup win in a row ({first}–{Y})." + tail}


def f_bigdog(H, Y, names):
    """Where the Big Dog's total ranks all-time."""
    I = H['ind']
    if Y not in I:
        return None
    win = min((x for x in I[Y] if x['pos']), key=lambda x: x['pos'], default=None)
    if not win or not win['tot']:
        return None
    rounds = len([s for s in win['r'] if s])
    pool = []
    for y, L in I.items():
        for x in L:
            if x['pos'] == 1 and x['tot'] and len([s for s in x['r'] if s]) == rounds:
                pool.append((x['tot'], y, x['p']))
    pool.sort(reverse=True)
    rank = 1 + sum(1 for t, y, p in pool if t > win['tot'])
    n = len(pool)
    if n < 5:
        return None
    yrs = sorted({y for t, y, p in pool})
    gaps = [y for y in range(yrs[0], yrs[-1] + 1) if y not in yrs]
    scope = (f"the {n} three-round tours with full scores on record ({yrs[0]} onwards"
             + ''.join(f"; {g} had only {max((len([v for v in x['r'] if v]) for x in I.get(g, [])), default=0) or 'fewer'} rounds" for g in gaps) + ")")
    level = [(y, p) for t, y, p in pool if t == win['tot'] and y != Y]
    joint = 'joint ' if level else ''
    withw = (', level with ' + ' and '.join(f"{names.get(p, p)} in {y}" for y, p in level)) if level else ''
    low_rank = 1 + sum(1 for t, y, p in pool if t < win['tot'])
    if rank <= 3:
        txt = (f"{poss(names.get(win['p'], win['p']))} {win['tot']} points is the {joint}"
               + ('highest' if rank == 1 else f'{ordn(rank)}-highest') + f" winning total in tour history{withw}. Ranked across {scope}.")
    elif low_rank <= 3:
        txt = (f"{names.get(win['p'], win['p'])} won with {win['tot']} points – the {joint}"
               + ('lowest' if low_rank == 1 else f'{ordn(low_rank)}-lowest') + f" winning total in tour history{withw}. Ranked across {scope}.")
    else:
        return None
    return {'type': 'bigdog', 'title': 'Big Dog by numbers', 'text': txt}


def f_round(H, Y, names):
    """A single-round score that ranks in the all-time top three."""
    I = H['ind']
    if Y not in I:
        return None
    allr = sorted([(s, y, x['p']) for y, L in I.items() for x in L for s in x['r'] if isinstance(s, (int, float))]
                  + [(e['s'], e['y'], e['p']) for e in H.get('extra', [])], reverse=True)
    mine = sorted(((s, x['p']) for x in I[Y] for s in x['r'] if isinstance(s, (int, float))), reverse=True)
    if not mine:
        return None
    s, p = mine[0]
    rank = 1 + sum(1 for a in allr if a[0] > s)
    if rank > 5:
        return None
    eq = sum(1 for a in allr if a[0] == s)
    who = list(dict.fromkeys(q for v, q in mine if v == s))
    whos = [names.get(q, q) for q in who]
    if len(whos) == 1:
        lead = f"{poss(whos[0])} {s} points " + ('(twice) ' if sum(1 for v, q in mine if v == s) > 1 else '') + 'is '
    else:
        lead = f"{', '.join(whos[:-1])} and {whos[-1]} each scored {s} points – "
    others = [(y, q) for v, y, q in allr if v == s and not (y == Y and q in who)]
    joint = 'joint ' if others or len(whos) > 1 else ''
    tail = (' (level with ' + ' and '.join(f"{names.get(q, q)} in {y}" for y, q in others) + ')') if others else ''
    top = allr[0]
    behind = (f", behind {poss(names.get(top[2], top[2]))} record {top[0]} in {top[1]}" if rank == 2 and not others else '')
    return {'type': 'round', 'title': 'One for the record books',
            'text': lead + (f'the {joint}best single round in tour history' if rank == 1 else
                    f"the {joint}{ordn(rank)}-best single round in tour history") + behind + tail + '.'}


def f_debut(H, Y, names):
    S = H['sheets']
    if Y not in S:
        return None
    if Y < 2006:  # team sheets start in 2004 and the 2002 line-up isn't recorded, so early debut counts are unreliable
        return None
    seen = {x['p'] for y, L in H['ind'].items() if y < Y for x in L}
    seen |= {p for y, L in H.get('early', {}).items() if y < Y for p in L}
    for y in sorted(S):
        if y >= Y:
            break
        seen |= set(S[y])
    new = [p for p in S[Y] if p not in seen]
    if not new or len(seen) == 0:
        return None
    ever = len(seen | set(S[Y]))
    nm = ', '.join(names.get(p, p) for p in new[:4]) + ('…' if len(new) > 4 else '')
    return {'type': 'debut', 'title': 'Fresh blood',
            'text': f"{len(new)} debutant{'s' if len(new) > 1 else ''} this year ({nm}), taking the number of dogs who "
                    f"have ever toured to {ever}."}


def _tours():
    import os, json
    here = os.path.dirname(os.path.abspath(__file__))
    for d in (os.environ.get('BDT_SRC', ''), os.path.dirname(here), '/mnt/user-data/uploads/Claude Workings For New Webpages'):
        f = os.path.join(d, 'bdt_tour_courses.html')
        if d and os.path.exists(f):
            cs = open(f, encoding='utf-8').read()
            return json.JSONDecoder().raw_decode(cs[cs.find('const D=') + 8:])[0]['tours']
    return []


def f_margin(H, Y, names):
    """Biggest / closest Ryder Cup result."""
    R = H['res']
    if Y not in R or R[Y]['w'] == 'H':
        return None
    m = {y: abs(v['bh'] - v['rt']) for y, v in R.items() if v['w'] != 'H'}
    mine = m[Y]; v = R[Y]; w = v['w']
    sc = f"{half(max(v['bh'], v['rt']))}–{half(min(v['bh'], v['rt']))}"
    big = sorted(m.values(), reverse=True)
    rank = 1 + sum(1 for x in m.values() if x > mine); eq = sum(1 for x in m.values() if x == mine)
    if rank <= 2:
        return {'type': 'margin', 'title': 'Biggest win', 'text': f"The {TEAM[w]}' {sc} win – a margin of {half(mine)} points – is " + ('the biggest' if rank == 1 else 'the 2nd-biggest')
                + f" winning margin in Ryder Cup history" + (f" (shared with {eq - 1} other{'s' if eq > 2 else ''})." if eq > 1 else '.')}
    low = 1 + sum(1 for x in m.values() if x < mine)
    if low <= 2 or mine <= 1:
        return {'type': 'margin', 'title': 'Too close to call', 'text': f"The {TEAM[w]} won {sc} – a margin of just {half(mine)} point{'s' if mine != 1 else ''}"
                + (f", one of the {eq} narrowest winning margins in the cup's history." if eq > 1 else ", the narrowest winning margin in the cup's history.")}
    return None


def f_place(H, Y, names):
    """Where this tour sits in the history of BDT destinations."""
    T = sorted(_tours(), key=lambda t: t['y'])
    t = next((x for x in T if x['y'] == Y), None)
    if not t:
        return None
    if Y == T[0]['y']:
        return {'type': 'place', 'title': 'Where it all began', 'text': f"The very first Big Dogs Tour – {t['loc']}{', ' + t['cty'] if t.get('cty') and t['cty'] != t['loc'] else ''}, {Y}. "
                f"{len(T)} tours and {len({x['cty'] for x in T})} countries later, the dogs are still touring."}
    before = [x for x in T if x['y'] < Y]
    same = [x for x in before if x['cty'] == t['cty']]
    tot = len([x for x in T if x['cty'] == t['cty']])
    if not same:
        n = len({x['cty'] for x in before}) + 1
        return {'type': 'place', 'title': 'New territory', 'text': f"The tour's first trip to {t['cty']} – the {ordn(n)} country the dogs had visited." +
                (f" They have been back {tot - 1} time{'s' if tot > 2 else ''} since." if tot > 1 else '')}
    loc_same = [x for x in before if x['loc'] == t['loc']]
    if loc_same:
        return {'type': 'place', 'title': 'Return visit', 'text': f"A return to {t['loc']}, last visited in {loc_same[-1]['y']}. "
                f"{t['cty']} has hosted {tot} tours in all."}
    top = max(tot, *(sum(1 for x in T if x['cty'] == c) for c in {x['cty'] for x in T}))
    return {'type': 'place', 'title': 'Familiar territory', 'text': f"Tour number {len(same) + 1} in {t['cty']} (after {', '.join(str(x['y']) for x in same)})."
            + (f" {t['cty']} has hosted {tot} tours in all – more than any other country." if tot == top else f" {t['cty']} has hosted {tot} tours in all.")}


def f_firstcup(H, Y, names):
    R = H['res']
    if not R or Y != min(R):
        return None
    v = R[Y]
    sc = f"{half(max(v['bh'], v['rt']))}–{half(min(v['bh'], v['rt']))}"
    return {'type': 'firstcup', 'title': 'Birth of the Ryder Cup',
            'text': f"The first Big Dogs Ryder Cup, Bloodhounds v Retrievers. " + (f"The {TEAM[v['w']]} won the inaugural cup {sc}." if v['w'] != 'H' else f"It finished all square, {sc}.")
            + f" {len(R)} cups have been played in all."}


TYPES = {'comeback': f_comeback, 'streak': f_streak, 'bigdog': f_bigdog, 'round': f_round, 'debut': f_debut, 'margin': f_margin, 'place': f_place, 'firstcup': f_firstcup}
ORDER = list(TYPES)


def pick(wb, Y, names, media):
    if media.get('fact') and media['fact'].get('text'):
        return dict(media['fact'], type='custom')
    H = load(wb)
    if media.get('fact_type') in TYPES:
        f = TYPES[media['fact_type']](H, Y, names)
        if f:
            return f
    f = f_firstcup(H, Y, names)
    if f:
        return f
    k = Y % len(ORDER)
    for t in ORDER[k:] + ORDER[:k]:
        f = TYPES[t](H, Y, names)
        if f:
            return f
    return None


def all_for(wb, Y, names):
    H = load(wb)
    return {t: fn(H, Y, names) for t, fn in TYPES.items()}
