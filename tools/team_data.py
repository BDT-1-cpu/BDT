"""Player profiles for Bloodhounds.html / Retrievers.html (webdata playerProfiles), from the Master Playbook:
caps and debut (Caps), trophy counts (Trophy Cabinet, plus Ryder Cups won or retained with the team),
and Ryder Cup record (RC Players, all teams combined). Photos, songs and anything else are kept."""
from update_site import norm

ORDER = ['Ryder Cup', 'Big Dog', '2nd', '3rd', 'Shitzu', 'Great Dane', 'St Bernard', 'Goblat', 'Rottweiler', 'Poodle',
         'Cheat', 'Xolo', 'Seve & Olly', 'Elton Ravo Prize', 'Duncan Goodhew']
TEAM = {'BH': 'Bloodhounds', 'RT': 'Retrievers'}


def _table(book, sheet):
    g = book.g[sheet]
    hi = next(i for i, r in enumerate(g) if norm(r[0]) == 'Name' and norm(r[1]) == 'Player')
    H = [norm(x) for x in g[hi]]
    out = {}
    for r in g[hi + 1:]:
        if norm(r[0]) == '':
            break
        out[norm(r[0])] = [norm(x) for x in r]
    return H, out


def cup_wins(book):
    """Cups won or retained while playing Ryder Cup matches for the side that won or kept it - including as a
    Mongrel for the other team (Gav 2012, Tully 2019 & 2022) and in spirit (Ollie Gobat 2014), but not as a
    non-playing tourist (Buzz 2024)."""
    holder = {norm(r[0]): norm(r[10]) for r in book.g['RC Results'] if isinstance(norm(r[0]), int) and norm(r[10])}
    won = {}
    for r in book.g['calc_Long']:
        y, t = norm(r[3]), norm(r[5])
        if isinstance(y, int) and holder.get(y) == TEAM.get(t):
            won.setdefault(norm(r[2]), set()).add(y)
    return {p: len(v) for p, v in won.items()}


def build(book, team, old):
    """team is 'BH' or 'RT'; old is the page's current playerProfiles. Returns the new playerProfiles."""
    _, caps = _table(book, 'Caps')
    th, cab = _table(book, 'Trophy Cabinet')
    _, rc = _table(book, 'RC Players')
    real = {norm(r[0]): norm(r[2]) for r in book.g['Players'][1:] if norm(r[0])}
    cups = cup_wins(book)
    out = {}
    for p, r in rc.items():
        if r[43] != team:
            continue
        o = dict(old.get(p, {}))
        o['team'] = team
        o['realName'] = o.get('realName') or real.get(p, p)
        o['caps'] = caps[p][2] if p in caps else 0
        o['debut'] = caps[p][3] if p in caps else None
        tro = {}
        for t in ORDER:
            if t == 'Ryder Cup':
                tro[t] = cups.get(p, 0)
            else:
                v = cab.get(p, [])[th.index(t)] if p in cab and t in th else 0
                tro[t] = int(v) if isinstance(v, (int, float)) else 0
        o['trophies'] = tro
        o['record'] = {'w': int(r[38] or 0), 'l': int(r[39] or 0), 'h': int(r[40] or 0)}
        out[p] = o
    return dict(sorted(out.items(), key=lambda kv: kv[0].lower()))
