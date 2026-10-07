"""Round-by-round data for Courses.html (const D.tours), worked out from the Master Playbook.

Fields that aren't in the Playbook (course display names/keys, tee-photo and scorecard image IDs,
round dates for old tours, country) are kept from the page; a new tour gets them from the
Tours sheet and its dates (round n = start date + n days)."""
import datetime, re
from update_site import norm

FMT = {'F': 'Fourball', 'S': 'Singles'}


def _year_rows(g):
    return [r for r in g[1:] if isinstance(norm(r[0]), int)]


def round_stats(book, year):
    team = {norm(r[3]): {'Bloodhounds': 'BH', 'Retrievers': 'RT'}.get(norm(r[1]), '')
            for r in _year_rows(book.g['Team Sheets']) if norm(r[0]) == year}
    ind = [r for r in _year_rows(book.g['Individual']) if norm(r[0]) == year]
    rc = [r for r in _year_rows(book.g['RC Matches']) if norm(r[0]) == year]
    out = {}
    for k in (1, 2, 3):
        sc = [(norm(r[1]), norm(r[1 + k])) for r in ind if isinstance(norm(r[1 + k]), (int, float))]
        sc.sort(key=lambda x: -x[1])        # stable: ties keep the sheet's order
        o = {}
        if sc:
            top = sc[0][1]
            o.update(best=[p for p, v in sc if v == top], pts=top,
                     avg=round(sum(v for _, v in sc) / len(sc), 2), n=len(sc),
                     all=[[p, v, team.get(p, '')] for p, v in sc])
        ms = [r for r in rc if norm(r[1]) == k and norm(r[10]) != 'Abandoned']
        if ms:
            bh = sum(norm(r[15]) or 0 for r in ms); rt = sum(norm(r[16]) or 0 for r in ms)
            o['rc'] = [bh, rt]
            fm = []
            for r in ms:
                f = norm(r[2]) or FMT.get(norm(r[14]), '')
                if f not in fm:
                    fm.append(f)
            o['fmt'] = '/'.join(sorted(fm, key=lambda f: f != 'Fourball'))
        out[k] = o
    return out


def tour_row(book, year):
    for r in book.g['Tours'][1:]:
        if norm(r[0]) == year:
            return [norm(x) for x in r]


def build(book, D, extras=None):
    """Returns D with every tour's round stats refreshed and any new Playbook year added."""
    tours = {int(t['y']): t for t in D['tours']}
    years = sorted(norm(r[0]) for r in book.g['Tours'][1:] if isinstance(norm(r[0]), int)
                   and any(norm(x[0]) == norm(r[0]) for x in _year_rows(book.g['Individual'])))
    for y in years:
        T = tour_row(book, y)
        stats = round_stats(book, y)
        if y not in tours:
            start = T[15]
            start = datetime.date.fromisoformat(str(start)[:10]) if start else None
            loc = str(T[1])
            place = loc.split(',')[0].strip()
            # country: from an earlier tour to the same place, or from "Place, Country" in the Tours sheet
            cty = next((t['cty'] for t in sorted(tours.values(), key=lambda t: -int(t['y'])) if t['loc'] == place), '')
            X = (extras or {}).get(y, {})
            cty = X.get('country') or cty
            if not cty and ',' in loc:
                cty = loc.split(',')[-1].strip()
            if not cty:
                print(f'Courses: no country known for {place} {y} - add "country" to {y}.json')
            tours[y] = {'y': y, 'loc': place, 'cty': cty, 'rounds': []}
            # a course played before keeps its key, so its history joins up on the Courses page
            seen = {}
            for t in tours.values():
                for o in t['rounds']:
                    seen.setdefault(o['c'].lower(), o['k']); seen.setdefault(o['k'].lower(), o['k'])
            for k in (1, 2, 3):
                c = T[3 + k]
                if not c:
                    continue
                days, names = X.get('round_days') or [], X.get('course_names') or []
                d = start + datetime.timedelta(days=k) if start else None
                day = days[k - 1] if len(days) >= k and days[k - 1] else (d.strftime('%a %-d %b') if d else '')
                full = names[k - 1] if len(names) >= k and names[k - 1] else c
                key = seen.get(full.lower()) or seen.get(c.lower()) or full
                tours[y]['rounds'].append({'r': k, 'c': key, 'k': key, 'd': day, 't': '', 'b': ''})
        for o in tours[y]['rounds']:
            st = stats.get(o['r'], {})
            for f in ('best', 'pts', 'avg', 'n', 'all', 'rc', 'fmt'):
                if f in st:
                    o[f] = st[f]
    D['tours'] = [tours[y] for y in sorted(tours)]
    return D
