#!/usr/bin/env python3
"""Rebuild every page that shows Playbook figures, from the Master Playbook.

    python3 tools/build_site.py "Big Dogs Tour - Master Playbook.xlsx" [--check] [--recalculated pb.xlsx]

Run it after tools/apply_results.py has added a tour (or after any change to the Playbook). It
  1. recalculates a copy of the Playbook with LibreOffice (the file itself is not changed),
  2. adds any new tour to bdt_team_results.csv (the Ryder Cup results list used by several pages),
  3. rebuilds Statistics, Trophies, Courses, Handicaps, Bloodhounds, Retrievers, Trivia and Home,
  4. rebuilds the Tours page and every tour-year page (BDT 2002.html ...) with build_tour_page.py, creating
     tour_media/<year>.json for a new tour if there isn't one (photos and videos are added to it by hand),
and prints what changed on each page. --check shows the changes without writing anything.
The Playbook must never be committed to this repository (it holds personal details).
"""
import argparse, csv, glob, io, json, os, re, shutil, subprocess, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import update_site as U                                   # noqa: E402
import courses_data, handicaps_data, team_data, trivia_data, home_data   # noqa: E402
from update_site import norm                              # noqa: E402

CSV = os.path.join(ROOT, 'bdt_team_results.csv')
CSV_FIELDS = ['year', 'bloodhounds', 'retrievers', 'result', 'cup_holders', 'note', 'venue', 'courses',
              'bloodhounds_players', 'retrievers_players']


# ---------------------------------------------------------------- helpers
def frac(v):
    """10.75 -> '10¾'"""
    v = float(v)
    w = int(v)
    f = round(v - w, 2)
    return (str(w) if w or not f else '') + {0.25: '¼', 0.5: '½', 0.75: '¾'}.get(f, '') if f else str(w)


def grab(s, key):
    """(value, start, end) of the JSON literal after `key` in a page"""
    i = s.index(key) + len(key)
    v, n = json.JSONDecoder().raw_decode(s[i:])
    return v, i, i + n


def dumps_like(v, raw):
    for kw in ({'ensure_ascii': False}, {}, {'separators': (',', ':'), 'ensure_ascii': False}, {'separators': (',', ':')}):
        if json.dumps(json.loads(raw), **kw) == raw:
            return json.dumps(v, **kw)
    return json.dumps(v, ensure_ascii=False)


def put(s, key, v):
    old, i, j = grab(s, key)
    return s if old == v else s[:i] + dumps_like(v, s[i:j]) + s[j:]


WEBDATA = re.compile(r'(<script id="webdata" type="application/json">)(.*?)(</script>)', re.S)


# ---------------------------------------------------------------- results list
def results_rows(book):
    """bdt_team_results.csv rows, adding any Playbook tour that isn't listed yet (existing rows are kept)."""
    with open(CSV, encoding='utf-8-sig') as f:
        rows = list(csv.DictReader(f))
    have = {r['year'] for r in rows}
    tours = {norm(r[0]): [norm(x) for x in r] for r in book.g['Tours'][1:] if isinstance(norm(r[0]), int)}
    real = {}
    for r in book.g['Team Sheets'][1:]:
        if isinstance(norm(r[0]), int):
            real.setdefault((norm(r[0]), norm(r[1])), []).append(
                (norm(r[2]) or 0, (norm(r[6]) or norm(r[5]) or norm(r[3])) + (' (c)' if norm(r[4]) == 'Y' else '')))
    added = []
    for r in book.g['RC Results']:
        y = norm(r[0])
        if not isinstance(y, int) or str(y) in have or not norm(r[10]):
            continue
        bh, rt, hold = norm(r[8]), norm(r[9]), norm(r[10])
        T = tours.get(y, [])
        result = 'Halved' if bh == rt else ('Bloodhounds' if bh > rt else 'Retrievers')
        rows.append({'year': str(y), 'bloodhounds': frac(bh), 'retrievers': frac(rt), 'result': result,
                     'cup_holders': hold,
                     'note': f'Halved – {hold} retain' if result == 'Halved' else f'{result} win',
                     'venue': (T[1] if T else norm(r[1])),
                     'courses': ', '.join(c for c in T[4:7] if c and c != 'N/A') if T else '',
                     'bloodhounds_players': ', '.join(n for _, n in sorted(real.get((y, 'Bloodhounds'), []))),
                     'retrievers_players': ', '.join(n for _, n in sorted(real.get((y, 'Retrievers'), [])))})
        added.append(y)
    rows.sort(key=lambda r: int(r['year']))
    return rows, added


def write_csv(rows):
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=CSV_FIELDS, lineterminator='\r\n')
    w.writeheader()
    w.writerows(rows)
    return '﻿' + buf.getvalue()


# ---------------------------------------------------------------- pages
def extras():
    """<year>.json files: per-tour website extras (country, round days, full course names, photos...)"""
    out = {}
    for f in glob.glob(os.path.join(ROOT, '[12][09][0-9][0-9].json')):
        try:
            out[int(os.path.basename(f)[:4])] = json.load(open(f, encoding='utf-8'))
        except ValueError:
            pass
    return out


def page_courses(s, book):
    D, _, _ = grab(s, 'const D=')
    return put(s, 'const D=', courses_data.build(book, D, extras()))


def page_handicaps(s, book, res):
    D, _, _ = grab(s, 'const D=')
    return put(s, 'const D=', handicaps_data.build(book, D, res))


def page_team(s, book, team):
    m = WEBDATA.search(s)
    W = json.loads(m.group(2))
    new = team_data.build(book, team, W['playerProfiles'])
    if new == W['playerProfiles']:
        return s
    W['playerProfiles'] = new
    return s[:m.start(2)] + dumps_like(W, m.group(2)) + s[m.end(2):]


def page_trivia(s, book, res):
    s = put(s, 'const D=', trivia_data.results(res))
    s = put(s, 'TROPH=', trivia_data.trophies(book))
    s = put(s, 'ROUNDS=', trivia_data.rounds(book))
    nk, _, _ = grab(s, 'NICK=')
    new = trivia_data.nick(book)
    return s if nk == new else put(s, 'NICK=', new)


def page_home(s, book, courses, res):
    links = json.load(open(os.path.join(ROOT, 'links.json'), encoding='utf-8'))
    return home_data.update(s, book, courses, res, links)


def tour_years(book):
    """Every year with results (Individual, Ryder Cup or trophies). The next tour's preview page is left alone."""
    ys = set()
    for sh in ('Individual', 'RC Matches', 'Trophies'):
        ys |= {norm(r[0]) for r in book.g[sh][1:] if isinstance(norm(r[0]), int)}
    return sorted(ys)


def stage_legacy(tmp, playbook, files):
    """A folder laid out the way build_tour_page.py / build_tours_page.py expect."""
    src, w = os.path.join(tmp, 'src'), os.path.join(tmp, 'w')
    media = os.path.join(w, 'tour_media')
    os.makedirs(os.path.join(media, 'boards'))
    shutil.copyfile(playbook, os.path.join(src if os.makedirs(src) is None else src, 'Big Dogs Tour - Master Playbook.xlsx'))
    open(os.path.join(src, 'bdt_tour_courses.html'), 'w', encoding='utf-8').write(files['Courses.html'])
    open(os.path.join(src, 'bdt_trophies.html'), 'w', encoding='utf-8').write(files['Trophies.html'])
    open(os.path.join(src, 'bdt_team_results.csv'), 'w', encoding='utf-8').write(files['bdt_team_results.csv'])
    for f in ('build_tour_page.py', 'build_tours_page.py', 'layout_g.py', 'facts.py', 'header_a.py',
              'header_themes.py', 'site_style.py', 'tour_page_template.html', 'tours_page_template.html'):
        shutil.copy(os.path.join(ROOT, f), w)
    for f in glob.glob(os.path.join(ROOT, 'tour_media', '*.json')) + glob.glob(os.path.join(ROOT, '[12][09][0-9][0-9].json')):
        shutil.copy(f, media)
    for f in ('extra_heads.json', 'events.json'):
        if os.path.exists(os.path.join(ROOT, f)):
            shutil.copy(os.path.join(ROOT, f), media)
    shutil.copyfile(os.path.join(ROOT, 'tours_index_v2.json'), os.path.join(media, 'tours_index.json'))
    for f in glob.glob(os.path.join(ROOT, 'BDT_*_*.jpg')):
        shutil.copy(f, os.path.join(media, 'boards'))
    return src, w


def blank_media(y):
    return {'_help': 'Per-tour extras that are NOT in the playbook. Image values are Wix media IDs (the 32-character '
                     'code after 588d17_ in the Wix image address). Videos use the Vimeo number.',
            'year': y, 'strapline': '', 'hero': {}, 'venue': {}, 'captains': {}, 'accommodation': {},
            'itinerary_images': [], 'itinerary_extra': {}, 'team_photos': {}, 'team_announcement': [],
            'rc_images': [], 'leaderboard_images': [], 'summary': {}, 'video_sections': [], 'gallery': [],
            'gallery_placeholder': f'The {y} photos are being sorted and will be added here shortly.',
            'video_placeholder': True}


def same_page(a, b):
    """True when two tour pages differ only in how their embedded pictures were compressed."""
    if a == b:
        return True
    try:
        Ta, i, j = grab(a, 'const T=')
        Tb, k, m = grab(b, 'const T=')
    except ValueError:
        return False
    if a[:i] + a[j:] != b[:k] + b[m:]:
        return False
    for key in ('rc_images', 'leaderboard_images'):
        if len(Ta['media'].get(key, [])) == len(Tb['media'].get(key, [])):
            Tb['media'][key] = Ta['media'].get(key, [])
    return Ta == Tb


def legacy_pages(book_path, files, years, new_media):
    out = {}
    with tempfile.TemporaryDirectory(prefix='bdt_build_') as tmp:
        src, w = stage_legacy(tmp, book_path, files)
        for y, m in new_media.items():
            json.dump(m, open(os.path.join(w, 'tour_media', f'{y}.json'), 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
        env = dict(os.environ, BDT_SRC=src)
        for y in years:
            r = subprocess.run([sys.executable, 'build_tour_page.py', str(y), '--out', f'bdt_tour_{y}.html'], cwd=w,
                               env=env, capture_output=True, text=True)
            if r.returncode:
                raise SystemExit(f'BDT {y}: build_tour_page.py failed\n{r.stderr[-2000:]}')
            out[f'BDT {y}.html'] = open(os.path.join(w, f'bdt_tour_{y}.html'), encoding='utf-8').read()
        r = subprocess.run([sys.executable, 'build_tours_page.py'], cwd=w, env=env, capture_output=True, text=True)
        if r.returncode:
            raise SystemExit(f'Tours: build_tours_page.py failed\n{r.stderr[-2000:]}')
        out['Tours.html'] = open(os.path.join(w, 'bdt_tours.html'), encoding='utf-8').read()
    return out


# ---------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('playbook')
    ap.add_argument('--check', action='store_true', help='show what would change without writing it')
    ap.add_argument('--recalculated', help='an already recalculated copy of the Playbook')
    a = ap.parse_args()
    pb = a.recalculated or U.recalculated(a.playbook)
    book = U.Book(pb)

    read = lambda f: open(os.path.join(ROOT, f), encoding='utf-8').read()
    before, after = {}, {}

    res, added = results_rows(book)
    before['bdt_team_results.csv'] = open(CSV, encoding='utf-8-sig').read()
    csv_text = write_csv(res) if added else '﻿' + before['bdt_team_results.csv']
    after['bdt_team_results.csv'] = csv_text.lstrip('﻿')

    spec = json.load(open(os.path.join(HERE, 'sitedata_spec.json')))
    for f in ('Statistics.html', 'Trophies.html'):
        before[f] = read(f)
        after[f] = U.rebuild_page(os.path.join(ROOT, f), book, spec)
    before['Courses.html'] = read('Courses.html')
    after['Courses.html'] = page_courses(before['Courses.html'], book)
    courses, _, _ = grab(after['Courses.html'], 'const D=')
    for f, fn in (('Handicaps.html', lambda s: page_handicaps(s, book, res)),
                  ('Bloodhounds.html', lambda s: page_team(s, book, 'BH')),
                  ('Retrievers.html', lambda s: page_team(s, book, 'RT')),
                  ('Facts & Figures.html', lambda s: page_trivia(s, book, res)),
                  ('Home.html', lambda s: page_home(s, book, courses, res))):
        before[f] = read(f)
        after[f] = fn(before[f])

    years = tour_years(book)
    new_media = {y: blank_media(y) for y in years
                 if not os.path.exists(os.path.join(ROOT, 'tour_media', f'{y}.json'))
                 and not os.path.exists(os.path.join(ROOT, f'{y}.json'))}
    files = {'Courses.html': after['Courses.html'], 'Trophies.html': after['Trophies.html'], 'bdt_team_results.csv': csv_text}
    for f, s in legacy_pages(pb, files, years, new_media).items():
        before[f] = read(f) if os.path.exists(os.path.join(ROOT, f)) else ''
        after[f] = before[f] if same_page(before[f], s) else s

    changed = [f for f in after if after[f] != before[f]]
    print('Results list: added ' + ', '.join(map(str, added)) if added else 'Results list: no new tours')
    for f in after:
        print(f'{f}: {"CHANGED" if f in changed else "no change"}')
    for f in ('Statistics.html', 'Trophies.html'):
        if f in changed:
            for c in U.diff(json.loads(WEBDATA.search(before[f]).group(2)), json.loads(WEBDATA.search(after[f]).group(2))):
                print('   ', c)
    if a.check:
        return
    for f in changed:
        with open(os.path.join(ROOT, f), 'w', encoding='utf-8-sig' if f.endswith('.csv') else 'utf-8', newline='') as fh:
            fh.write(after[f])
    for y, m in new_media.items():
        json.dump(m, open(os.path.join(ROOT, f'{y}.json'), 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
        print(f'Created {y}.json for the {y} tour photos and videos')


if __name__ == '__main__':
    main()
