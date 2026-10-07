"""Data for Handicaps.html (const D), worked out from the Master Playbook's Handicaps, Team Sheets,
Individual, RC Matches, Players and Tours sheets plus bdt_team_results.csv."""
import re
from update_site import norm

TEAM = {'Bloodhounds': 'B', 'Retrievers': 'R'}


def _yr(g):
    return [r for r in g[1:] if isinstance(norm(r[0]), int)]


def build(book, old, res):
    g = book.g['Handicaps']
    hi = next(i for i, r in enumerate(g) if norm(r[0]) == 'Name' and norm(r[1]) == 'Player')
    hdr = g[hi]
    cols, ynote = {}, {}
    for c, h in enumerate(hdr[2:], 2):
        m = re.fullmatch(r'(\d{4})(\**\^?)', str(norm(h)))
        if m:
            cols[int(m.group(1))] = c
            if m.group(2):
                ynote[m.group(1)] = m.group(2)
    H, notes = {}, dict(old.get('notes', {}))
    for r in g[hi + 1:]:
        p = norm(r[0])
        if not p:
            continue
        if str(p).startswith('*'):
            m = re.match(r'(\*+)\s*(.*)', p)
            notes[m.group(1)] = m.group(2)
            continue
        h = {}
        for y, c in cols.items():
            v = norm(r[c])
            if v == '' or v is None:
                continue
            if isinstance(v, str):
                m = re.fullmatch(r'(\d+)(\*+)', v)
                h[str(y)] = [int(m.group(1)), m.group(2)] if m else [v]
            else:
                h[str(y)] = [int(v) if float(v).is_integer() else v]
        if h:
            H[p] = h
    years = sorted({int(y) for p in H for y in H[p]})
    # Years attended. Past tours keep the page's list, which includes cases only the notes record
    # (e.g. Buzz 2024 as a non-playing tourist; Ollie Gobat 2014 played only in spirit). A new tour
    # counts anyone with an Individual, Ryder Cup or trophy row (an Elton Ravo Prize alone doesn't count).
    known = max((y for v in old.get('att', {}).values() for y in v), default=0)
    att = {p: set(v) for p, v in old.get('att', {}).items()}
    for sh in ('Individual', 'RC Matches', 'Trophies'):
        for r in _yr(book.g[sh]):
            if norm(r[0]) <= known or (sh == 'Trophies' and norm(r[1]) == 'Elton Ravo Prize'):
                continue
            ps = {'Individual': [norm(r[1])], 'RC Matches': [norm(x) for x in r[4:8]], 'Trophies': [norm(r[2])]}[sh]
            for p in ps:
                if p:
                    att.setdefault(p, set()).add(norm(r[0]))
    team = {}
    for r in _yr(book.g['Team Sheets']):
        y, p = str(norm(r[0])), norm(r[3])
        t = team.setdefault(p, {})
        t[y] = TEAM.get(norm(r[1]), '')
        if norm(r[4]) == 'Y':
            t[y + 'c'] = 1
    names = {}
    for r in book.g['Players'][1:]:
        if norm(r[0]):
            names[norm(r[0])] = {'real': norm(r[2]) or norm(r[0]), 'web': norm(r[15]) or norm(r[2]) or norm(r[0])}
    tours = {str(norm(r[0])): norm(r[1]) for r in _yr(book.g['Tours'])}
    D = dict(old)
    D.update(H=H, years=years, ynote=ynote, notes=notes,
             att={p: sorted(v) for p, v in att.items()}, team=team, names=names,
             res={r['year']: {'b': r['bloodhounds'], 'r': r['retrievers'], 'res': r['result'], 'hold': r['cup_holders'],
                              'venue': r['venue']} for r in res},
             tours=tours)
    return D
