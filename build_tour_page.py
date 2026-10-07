#!/usr/bin/env python3
"""
Build a Big Dogs Tour year page (bdt_tour_<year>.html) from:
  - the Master Playbook workbook (tours, teams, Ryder Cup matches, individual scores, trophies, shirts)
  - bdt_tour_courses.html (course tee photos / scorecard Wix IDs, round dates, player head-shots, crest)
  - bdt_trophies.html (trophy icons and one-line descriptions)
  - tour_media/<year>.json (per-tour photos that aren't in the playbook: hero, captains, accommodation, gallery ...)
and the shared template tour_page_template.html.

Usage:  python3 build_tour_page.py 2024  [--out bdt_tour_2024.html]
"""
import json, re, sys, datetime, argparse, os
import openpyxl

HERE = os.path.dirname(os.path.abspath(__file__))
# Source files live in the folder above this one (Claude Workings For New Webpages); override with BDT_SRC
_parent = os.path.dirname(HERE)
SRC = os.environ.get('BDT_SRC') or (_parent if os.path.exists(os.path.join(_parent, 'Big Dogs Tour - Master Playbook.xlsx'))
                                    else '/mnt/user-data/uploads/Claude Workings For New Webpages')
PLAYBOOK = os.path.join(SRC, 'Big Dogs Tour - Master Playbook.xlsx')
COURSES = os.path.join(SRC, 'bdt_tour_courses.html')
TROPHIES = os.path.join(SRC, 'bdt_trophies.html')
TEMPLATE = os.path.join(HERE, 'tour_page_template.html')

FLAGS = {'Spain': 'es', 'Portugal': 'pt', 'Turkey': 'tr', 'UAE': 'ae', 'United Arab Emirates': 'ae', 'USA': 'us',
         'Sweden': 'se', 'Cyprus': 'cy', 'England': 'gb-eng', 'Wales': 'gb-wls', 'Morocco': 'ma', 'Scotland': 'gb-sct',
         'Ireland': 'ie', 'France': 'fr', 'Italy': 'it'}

TROPHY_ORDER = ['Big Dog', '2nd', '3rd', 'Shitzu', 'Goblat', 'Great Dane', 'St Bernard', 'Seve & Olly', 'Seve & Ollie', 'Xolo',
                'Rottweiler', 'Poodle', 'Cheat', 'Ashley Hurst Award', 'Elton Ravo Prize', 'Duncan Goodhew']
# playbook trophy name -> (display name, icon/description key on the Trophies page)
TROPHY_META = {
    'Big Dog': ('The Big Dog', 'Green Jacket'), '2nd': ('Second Place', '2nd'), '3rd': ('Third Place', '3rd'),
    'Shitzu': ('Shitzu', 'Shitzu'), 'Goblat': ('Goblat', 'Goblat'), 'Great Dane': ('Great Dane', 'Great Dane'),
    'St Bernard': ('St Bernard', 'St Bernard'), 'Seve & Olly': ('Seve & Olly', 'Seve & Olly'), 'Seve & Ollie': ('Seve & Olly', 'Seve & Olly'),
    'Xolo': ('Xolo', 'Bandit'), 'Rottweiler': ('Rottweiler', 'Rottweiler'), 'Poodle': ('Poodle', 'Poodle'),
    'Cheat': ('Cheat', 'Cheat'), 'Ashley Hurst Award': ('Cheat', 'Cheat'), 'Elton Ravo Prize': ('Elton Ravo Prize', 'Elton Ravo Prize'),
    'Duncan Goodhew': ('Duncan Goodhew', 'Duncan Goodhew'),
}


def rows(ws):
    r = list(ws.iter_rows(values_only=True))
    return r[0], r[1:]


def num(v):
    return None if v in (None, '', 'N/A') else float(v)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('year', type=int)
    ap.add_argument('--out')
    a = ap.parse_args()
    Y = a.year

    wb = openpyxl.load_workbook(PLAYBOOK, data_only=True, read_only=True)

    # ---- Tours row ----
    th, tours = rows(wb['Tours'])
    tour = next(r for r in tours if r[0] == Y)
    col = lambda txt: next(k for k, h in enumerate(th) if h and str(h).lower().startswith(txt.lower()))
    rc_played = str(tour[col('Ryder Cup played')]).strip().lower() == 'yes'
    bh_cap, rt_cap = tour[col('Bloodhounds captain')], tour[col('Retrievers captain')]
    override = tour[col('Winner override')]
    start, end = tour[col('Tour start date')], tour[col('Tour end date')]
    rc_num = tour[col('RC tour #')]
    players_on_tour = tour[col('Players on tour')]
    # previous cup holders
    holders = {}
    for r in tours:
        if r[0] is None or r[0] >= Y:
            continue
    # use the team-results csv style logic: compute holders from RC matches of every year < Y
    _, rcm = rows(wb['RC Matches'])
    by_year = {}
    for r in rcm:
        if r[0] is None or r[10] == 'Abandoned':
            continue
        b, t = by_year.setdefault(r[0], [0.0, 0.0]), None
        b[0] += float(r[15] or 0)
        b[1] += float(r[16] or 0)
    holder = None
    ovr = {r[0]: r[col('Winner override')] for r in tours if r[0]}
    for y in sorted(k for k in by_year if k < Y):
        bh, rt = by_year[y]
        if ovr.get(y):
            holder = 'BH' if 'blood' in str(ovr[y]).lower() else 'RT'
        elif bh > rt:
            holder = 'BH'
        elif rt > bh:
            holder = 'RT'
    holders_before = holder

    # ---- courses page data (tee / scorecard ids, dates, names, heads, crest) ----
    cs = open(COURSES, encoding='utf-8').read()
    i = cs.find('const D=') + 8
    D, _ = json.JSONDecoder().raw_decode(cs[i:])
    i = cs.find('HEAD={') + 5
    HEAD, _ = json.JSONDecoder().raw_decode(cs[i:])
    _xh = os.path.join(HERE, 'tour_media', 'extra_heads.json')  # headshots missing from the Courses page (e.g. 2026 debutants)
    if os.path.exists(_xh):
        for _k, _v in json.load(open(_xh)).items():
            HEAD.setdefault(_k, _v)
    crest = re.search(r'<img class="bdt-crest" src="(data:image/png;base64,[^"]+)"', cs).group(1)
    ctour = next((t for t in D['tours'] if t['y'] == Y), None)

    # ---- trophies page icons + descriptions ----
    ts = open(TROPHIES, encoding='utf-8').read()
    j0 = ts.find('var TROPHY_TAB_ICON = {'); j1 = ts.find('};', j0)
    ICONS = dict(re.findall(r"'([^']+)':\s*'(data:image/[^']+)'", ts[j0:j1]))
    # larger trophy photos (used on the Trophy Cabinet) – preferred over the small icons
    BIG = dict(re.findall(r"label:\s*'([^']+)',\s*img:\s*'(data:image/[a-z]+;base64,[A-Za-z0-9+/=]+)'", ts))
    for k, v in BIG.items():
        ICONS[k] = v
    ICONS.setdefault('Green Jacket', BIG.get('Green Jacket', ''))
    j0 = ts.find('var DESC = {'); j1 = ts.find('};', j0)
    DESC = dict(re.findall(r"'([^']+)':\s*'([^']*)'", ts[j0:j1]))

    # ---- players ----
    ph, prow = rows(wb['Players'])
    names = dict(D['names'])
    pcol = {h: k for k, h in enumerate(ph) if h}
    web_col = next((k for h, k in pcol.items() if 'website' in str(h).lower()), None)
    for r in prow:
        if r[0] and web_col is not None and r[web_col]:
            names[r[0]] = r[web_col]

    # ---- team sheets ----
    _, tsr = rows(wb['Team Sheets'])
    teams = {'BH': [], 'RT': []}
    for r in tsr:
        if r[0] == Y and r[1]:
            k = 'BH' if r[1].startswith('Blood') else 'RT'
            teams[k].append({'p': r[3], 'pos': r[2], 'cap': (r[4] == 'Y'), 'note': r[9] or ''})
            if r[6]:
                names[r[3]] = r[6]
    for k in teams:
        teams[k].sort(key=lambda x: x['pos'] or 99)

    # ---- matches ----
    matches = []
    for r in rcm:
        if r[0] != Y:
            continue
        bh = [p for p in (r[4], r[5]) if p]
        rt = [p for p in (r[6], r[7]) if p]
        res = {'Bloodhounds': 'BH', 'Retrievers': 'RT', 'Halved': 'H'}.get(r[8], r[8])
        matches.append({'r': r[1], 'fmt': r[2], 'v': r[3], 'bh': bh, 'rt': rt, 'res': res, 'm': r[9] or '',
                        'status': r[10] or 'Played', 'note': r[11] or '', 'pb': r[15] or 0, 'pr': r[16] or 0,
                        'holes': r[19] or 0})

    # ---- individual ----
    _, ind = rows(wb['Individual'])
    team_of = {}
    for k in teams:
        for x in teams[k]:
            team_of[x['p']] = k
    indiv = []
    for r in ind:
        if r[0] != Y or not r[1]:
            continue
        sc = [r[2], r[3], r[4]]
        indiv.append({'p': r[1], 'r': sc, 'tot': r[7] if isinstance(r[7], (int, float)) else None, 'pos': r[5], 'team': r[8] or team_of.get(r[1], '')})
    indiv.sort(key=lambda x: (x['pos'] if isinstance(x['pos'], (int, float)) else 998 if x['pos'] else 999, -(x['tot'] or 0)))  # MC after the placed players
    # a round nobody has a score for (e.g. 2012 Round III, rained off): show the real total of the rounds
    # that were played rather than the Playbook's scaled-up figure, and flag the round as abandoned
    abandoned_rounds = sorted({m['r'] for m in matches} - {m['r'] for m in matches if m.get('status') != 'Abandoned'})
    if abandoned_rounds:
        for x in indiv:
            pl = [v for v in x['r'] if isinstance(v, (int, float))]
            if pl:
                x['tot'] = sum(pl)

    # ---- trophies ----
    _, tro = rows(wb['Trophies'])
    tmap = {}
    for r in tro:
        if r[0] != Y or not r[1]:
            continue
        tmap.setdefault(r[1], {'w': [], 'why': ''})
        tmap[r[1]]['w'].append(r[2])
        if r[3] and not tmap[r[1]]['why']:
            tmap[r[1]]['why'] = str(r[3])
    trophies = []
    for key in TROPHY_ORDER + [k for k in tmap if k not in TROPHY_ORDER]:
        if key not in tmap:
            continue
        disp, ik = TROPHY_META.get(key, (key, key))
        tot = None
        if key in ('Big Dog', '2nd', '3rd', 'Shitzu'):
            w = next((x for x in indiv if x['p'] == tmap[key]['w'][0]), None)
            tot = w['tot'] if w else None
        trophies.append({'k': key, 'name': disp, 'alias': key if key in ('Cheat', 'Ashley Hurst Award') else '',
                         'desc': DESC.get(ik, ''), 'icon': ICONS.get(ik, ''), 'w': tmap[key]['w'],
                         'why': tmap[key]['why'], 'pts': tot})

    # ---- shirts ----
    _, wm = rows(wb['Website Media'])
    shirts = {'BH': {}, 'RT': {}}
    for r in wm:
        if r[0] == Y and r[4]:
            k = 'BH' if str(r[1]).startswith('Blood') else 'RT'
            mid = re.search(r'588d17_([0-9a-f]{32})', str(r[4]))
            if mid:
                shirts[k][{'Shirt': 'shirt', 'Shirt logo': 'logo', 'Team photo': 'photo'}.get(r[2], r[2])] = mid.group(1)

    # ---- rounds ----
    rounds = []
    if ctour:
        for o in ctour['rounds']:
            rounds.append({'r': o['r'], 'c': o['c'], 'd': o['d'], 'tee': o.get('t'), 'card': o.get('b'),
                           'best': o.get('best') or [], 'pts': o.get('pts'), 'avg': o.get('avg'),
                           'fmt': o.get('fmt') or '', 'rc': o.get('rc')})
    else:
        for n, c in enumerate(tour[col('Round I course'):col('Round III course') + 1], 1):
            if c and c != 'N/A':
                rounds.append({'r': n, 'c': c, 'd': '', 'best': [], 'pts': None, 'avg': None, 'fmt': ''})

    media = json.load(open(os.path.join(HERE, 'tour_media', f'{Y}.json'), encoding='utf-8'))
    # image lists may hold local file paths (relative to tour_media) -> embed them in the page
    import base64
    def embed(x):
        if isinstance(x, str) and x.lower().endswith(('.jpg', '.jpeg', '.png')):
            fp = os.path.join(HERE, 'tour_media', x)
            mime = 'image/png' if x.lower().endswith('.png') else 'image/jpeg'
            return f'data:{mime};base64,' + base64.b64encode(open(fp, 'rb').read()).decode()
        return x
    for key in ('rc_images', 'leaderboard_images'):
        media[key] = [embed(x) for x in media.get(key) or []]

    # everyone who appears anywhere gets a name + head-shot
    people = set(team_of) | {x['p'] for x in indiv} | {w for t in trophies for w in t['w']} | {bh_cap, rt_cap}
    people.discard(None)
    loc = ctour['loc'] if ctour else tour[1]
    cty = ctour['cty'] if ctour else tour[1]

    bh_pts = sum(m['pb'] for m in matches if m['status'] != 'Abandoned')
    rt_pts = sum(m['pr'] for m in matches if m['status'] != 'Abandoned')

    T = {
        'year': Y, 'loc': loc, 'cty': cty, 'flag': FLAGS.get(cty, ''), 'strap': media.get('strapline', ''),
        'start': start.strftime('%Y-%m-%d') if isinstance(start, datetime.datetime) else '',
        'end': end.strftime('%Y-%m-%d') if isinstance(end, datetime.datetime) else '',
        'players': players_on_tour, 'rcNum': rc_num, 'rcPlayed': rc_played,
        'cap': {'BH': bh_cap, 'RT': rt_cap}, 'holdersBefore': holders_before, 'override': override or '',
        'score': {'BH': bh_pts, 'RT': rt_pts},
        'names': {p: names.get(p, p) for p in people}, 'heads': {p: HEAD[p] for p in people if p in HEAD},
        'teams': teams, 'rounds': rounds, 'matches': matches, 'indiv': indiv, 'trophies': trophies,
        'shirts': shirts, 'media': media, 'rcTrophy': ICONS.get('Big Dogs Ryder Cup', ''),
    }
    import facts
    T['fact'] = facts.pick(wb, Y, names, media)
    T['abandonedRounds'] = abandoned_rounds
    try:
        import csv
        for _r in csv.DictReader(open(os.path.join(SRC, 'bdt_team_results.csv'), encoding='utf-8-sig')):
            if str(_r.get('year')) == str(Y) and _r.get('note') and not _r['note'].endswith(' win'):
                T['rcNote'] = _r['note']
    except Exception as _e:
        print('team results note skipped:', _e)
    print('interesting fact:', T['fact'])
    tpl = open(TEMPLATE, encoding='utf-8').read()
    out = tpl.replace('__CREST__', crest).replace('__YEAR__', str(Y)) \
             .replace('/*__TOUR_DATA__*/null', json.dumps(T, ensure_ascii=False, separators=(',', ':')))
    import header_a
    tidx = json.load(open(os.path.join(HERE, 'tour_media', 'tours_index.json'), encoding='utf-8'))['tours']
    photo = header_a.wix(media.get('header_photo') or tidx.get(str(Y), {}).get('img', ''))
    out = header_a.apply(out, f'Big Dogs Tour <span class="bdt-yr">{Y}</span>', f'{loc} · {cty}' if cty and cty != loc else loc, photo,
                           kicker=None if matches else '<span class="vs">THE EARLY YEARS · BEFORE THE RYDER CUP</span>')
    import layout_g
    out = layout_g.header_details(out, T.get('flag', ''), T.get('strap', ''), start if isinstance(start, datetime.datetime) else None,
                                  end if isinstance(end, datetime.datetime) else None, rc_num if matches else None)
    out = layout_g.apply(out)
    dst = a.out or os.path.join(HERE, f'bdt_tour_{Y}.html')
    open(dst, 'w', encoding='utf-8').write(out)
    print('wrote', dst, len(out) // 1024, 'KB')


if __name__ == '__main__':
    main()
