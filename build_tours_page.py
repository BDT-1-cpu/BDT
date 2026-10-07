#!/usr/bin/env python3
"""Builds bdt_tours.html – the Tours landing page (one statement photo per tour).
Data: bdt_team_results.csv (Ryder Cup results), Master Playbook (Big Dog winners),
bdt_tour_courses.html (locations, head-shots, crest) and tour_media/tours_index.json (photos + links)."""
import json, re, csv, os
import openpyxl

HERE = os.path.dirname(os.path.abspath(__file__))
_parent = os.path.dirname(HERE)
SRC = os.environ.get('BDT_SRC') or (_parent if os.path.exists(os.path.join(_parent, 'Big Dogs Tour - Master Playbook.xlsx'))
                                    else '/mnt/user-data/uploads/Claude Workings For New Webpages')
FLAGS = {'Spain': 'es', 'Portugal': 'pt', 'Turkey': 'tr', 'UAE': 'ae', 'USA': 'us', 'Sweden': 'se', 'Cyprus': 'cy',
         'England': 'gb-eng', 'Wales': 'gb-wls', 'Morocco': 'ma'}

cs = open(os.path.join(SRC, 'bdt_tour_courses.html'), encoding='utf-8').read()
D, _ = json.JSONDecoder().raw_decode(cs[cs.find('const D=') + 8:])
HEAD, _ = json.JSONDecoder().raw_decode(cs[cs.find('HEAD={') + 5:])
crest = re.search(r'<img class="bdt-crest" src="(data:image/png;base64,[^"]+)"', cs).group(1)

rc = {}
with open(os.path.join(SRC, 'bdt_team_results.csv'), encoding='utf-8-sig') as f:
    for r in csv.DictReader(f):
        rc[int(r['year'])] = {'bh': r['bloodhounds'], 'rt': r['retrievers'], 'res': r['result'], 'hold': r['cup_holders'],
                              'note': r['note']}

wb = openpyxl.load_workbook(os.path.join(SRC, 'Big Dogs Tour - Master Playbook.xlsx'), data_only=True, read_only=True)
bigdog = {}
for r in list(wb['Trophies'].iter_rows(values_only=True))[1:]:
    if r[1] == 'Big Dog' and r[0]:
        bigdog.setdefault(r[0], []).append(r[2])
th, tours = (lambda x: (x[0], x[1:]))(list(wb['Tours'].iter_rows(values_only=True)))
col = lambda t: next(k for k, h in enumerate(th) if h and str(h).lower().startswith(t.lower()))
players = {r[0]: r[col('Players on tour')] for r in tours if r[0]}
dates = {r[0]: (r[col('Tour start date')], r[col('Tour end date')]) for r in tours if r[0]}

idx = json.load(open(os.path.join(HERE, 'tour_media', 'tours_index.json'), encoding='utf-8'))
names = D['names']
out = []
for t in D['tours']:
    y = t['y']
    m = idx['tours'].get(str(y), {})
    s, e = dates.get(y, (None, None))
    bd = bigdog.get(y, [])
    out.append({'y': y, 'loc': m.get('loc') or t['loc'], 'cty': t['cty'], 'flag': FLAGS.get(t['cty'], ''),
                'img': m.get('img', ''), 'link': m.get('link', f'/bdt-{y}'), 'nick': m.get('nick', ''),
                'month': s.strftime('%B') if s else '', 'players': players.get(y),
                'rc': rc.get(y), 'bigdog': [{'n': names.get(p, p), 'h': HEAD.get(p, '')} for p in bd],
                'courses': [o['c'] for o in t['rounds']]})
data = {'tours': out, 'site': idx.get('site', 'https://www.bigdogstour.com')}
tpl = open(os.path.join(HERE, 'tours_page_template.html'), encoding='utf-8').read()
html = tpl.replace('__CREST__', crest).replace('/*__DATA__*/null', json.dumps(data, ensure_ascii=False, separators=(',', ':')))
import header_a
first, last = out[0]['y'], out[-1]['y']
html = header_a.apply(html, 'Big Dogs Tour', f'The Tours · {first}–{last}', '', extra_class='mosaic', photo_style='')
# mosaic of every tour's statement photo behind the heading (newest first), each tile links to that tour
tiles = sorted([t for t in out if t['img']], key=lambda t: -t['y'])
tiles = (tiles * 2)[:27]
site = idx.get('site', 'https://www.bigdogstour.com')
mos = '<div class="bdt-mosaic" aria-hidden="true">' + ''.join(
    f'<span><img src="{header_a.wix(t["img"], 320, 240)}" alt="" loading="eager"><i>{t["y"]}</i></span>'
    for t in tiles) + '</div>'
html = html.replace('<header class="bdt-hero mosaic" >', '<header class="bdt-hero mosaic">' + mos, 1)
assert 'bdt-mosaic' in html
open(os.path.join(HERE, 'bdt_tours.html'), 'w', encoding='utf-8').write(html)
print('wrote bdt_tours.html', len(html) // 1024, 'KB')
