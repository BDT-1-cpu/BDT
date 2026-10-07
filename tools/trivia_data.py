"""Data for the Trivia page (Facts & Figures.html), worked out from the Master Playbook and bdt_team_results.csv:
D (one entry per Ryder Cup, with both teams), TROPH (every trophy won, with real names), ROUNDS (Ryder Cup
points per round) and NICK (real name -> tour name). Photos, maps and the 2002-03 lists are kept."""
from update_site import norm


def _yr(g):
    return [r for r in g[1:] if isinstance(norm(r[0]), int)]


def names(book):
    """tour name -> name used on the site"""
    out = {}
    for r in book.g['Players'][1:]:
        if norm(r[0]):
            out[norm(r[0])] = norm(r[15]) or norm(r[2]) or norm(r[0])
    return out


def results(res):
    def pl(x):
        return [{'n': p.replace('(c)', '').strip(), 'c': '(c)' in p} for p in x.split(',') if p.strip()]
    return [{'y': int(r['year']), 'b': r['bloodhounds'], 'r': r['retrievers'], 'res': r['result'], 'hold': r['cup_holders'],
             'note': r['note'], 'venue': r['venue'], 'courses': r['courses'], 'bp': pl(r['bloodhounds_players']),
             'rp': pl(r['retrievers_players'])} for r in res]


def trophies(book):
    web = names(book)
    out = []
    for r in _yr(book.g['Trophies']):
        if not norm(r[2]):
            continue
        out.append({'y': norm(r[0]), 't': norm(r[1]), 'w': [web.get(norm(r[2]), norm(r[2]))], 'why': norm(r[3]) or ''})
    return out


def rounds(book):
    pts = {}
    for r in _yr(book.g['RC Matches']):
        y, k = norm(r[0]), norm(r[1])
        if not isinstance(k, int):
            continue
        R = pts.setdefault(str(y), {})
        if norm(r[10]) == 'Abandoned':
            R.setdefault(k, None)
            continue
        cur = R.get(k) or [0.0, 0.0]
        cur[0] += float(norm(r[15]) or 0); cur[1] += float(norm(r[16]) or 0)
        R[k] = cur
    return {y: [R.get(k) for k in (1, 2, 3)] for y, R in sorted(pts.items())}


def nick(book):
    web = names(book)
    return dict(sorted(((w, p) for p, w in web.items()), key=lambda kv: kv[0]))
