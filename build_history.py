"""Builds bdt_history.html (History page embed) from history_template.html + events.json.
   events.json: one entry per event {d: dd/mm/yyyy, t: text, img: Wix media id (32 hex, '' for none),
   c: tour|jacket|trophy|mde|first|rip, y: year}. Add new events there and re-run."""
import os, sys, json
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
import header_themes
ev = json.load(open(os.path.join(HERE, 'events.json'), encoding='utf-8'))
ev.sort(key=lambda e: (e['d'][6:], e['d'][3:5], e['d'][:2]))  # stable: keeps the listed order within a day
D = header_themes._courses()
idx = json.load(open(os.path.join(ROOT, 'tour_media', 'tours_index.json'), encoding='utf-8'))['tours']
tours = {str(t['y']): {'loc': f"{t['loc']}, {t['cty']}" if t['cty'] != t['loc'] else t['loc'],
                       'link': idx.get(str(t['y']), {}).get('link', '')} for t in D['tours']}
years = sorted({e['y'] for e in ev})
nums = [(len(D['tours']), 'Tours'), (len(ev), 'Moments'), (len({t['cty'] for t in D['tours']}), 'Countries')]
intro = ("From the first email Hursty sent to his fellow Inaugurals in August 2002 to the latest tour, "
         "these are the moments that made the Big Dogs Tour – the tours, the Green Jackets, the trophies, the MDEs and the firsts. "
         "<b>Use the buttons to show one kind of moment, jump to a year, or tap any photo to enlarge it.</b>")
h = open(os.path.join(HERE, 'history_template.html'), encoding='utf-8').read()
crest = open(os.path.join(ROOT, 'home', 'crest.txt')).read()
rep = {'CREST': crest, 'INTRO': intro, 'NUMS': ''.join(f'<div><b>{a}</b><i>{b}</i></div>' for a, b in nums),
       'EVENTS': json.dumps([{k: e[k] for k in ('d', 't', 'img', 'c', 'y')} for e in ev], ensure_ascii=False),
       'TOURS': json.dumps(tours, ensure_ascii=False)}
for k, v in rep.items():
    h = h.replace('{{' + k + '}}', str(v))
h = header_themes.apply(h, 'History · 2002–' + years[-1], 'history')
out = os.path.join(ROOT, 'bdt_history.html')
open(out, 'w', encoding='utf-8').write(h)
print('wrote', out, len(h) // 1024, 'KB,', len(ev), 'events')
