#!/usr/bin/env python3
"""Turns tour_media/bdt_media_all.json (everything collected from the old BDT year pages) into
tour_media/<year>.json files in the same shape as 2024.json.  Existing hand-edited fields
(accommodation name/blurb, summary text, fact, etc.) in an existing <year>.json are kept."""
import json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
TM = os.path.join(HERE, 'tour_media')
A = json.load(open(os.path.join(TM, 'bdt_media_all.json'), encoding='utf-8'))
VI = json.load(open(os.path.join(TM, 'bdt_vimeo_info.json'), encoding='utf-8'))
cs = open(os.path.join(os.environ.get('BDT_SRC', '/mnt/user-data/uploads/Claude Workings For New Webpages'), 'bdt_tour_courses.html'), encoding='utf-8').read()
D = json.JSONDecoder().raw_decode(cs[cs.find('const D=') + 8:])[0]
LOC = {t['y']: (t['loc'], t['cty']) for t in D['tours']}
HELP = json.load(open(os.path.join(TM, '2024.json'), encoding='utf-8'))['_help']
ORDER = ['venue', 'captains', 'accommodation', 'itinerary', 'courses', 'teams', 'announcement', 'rydercup', 'leaderboard',
         'summary', 'slideshow', 'videos', 'trophies', 'photos']
hid = lambda s: re.search(r'([0-9a-f]{32})', s).group(1)


def vid(it):
    v = it.get('vimeo'); i = VI.get(v, {})
    d = {'vimeo': v, 'title': (i.get('t') or it.get('title') or '').strip()}
    if i.get('th'):
        d['thumb'] = i['th']
    return d


def build(y, o):
    Y = int(y)
    heads = o['heads']
    vy = next((h['y'] for h in heads if h['key'] == 'venue'), None)
    # headings above THE VENUE are page titles/straplines (e.g. "VILLA EL CANINE"), not sections
    heads = [h for h in heads if vy is None or h['y'] >= vy - 5]
    def sec(yy):
        s = 'header'
        for h in heads:
            if yy >= h['y'] - 5:
                s = h['key']
        return s
    items = o['items']
    for it in items:
        it['s'] = sec(it['y'])
    keys = [h['key'] for h in heads]
    # 2012-14: the villa had no ACCOMMODATION heading, so its gallery sits under THE CAPTAINS
    if 'accommodation' not in keys:
        for it in items:
            if it['kind'] == 'gallery' and it['s'] == 'captains':
                it['s'] = 'accommodation'
    by = lambda s, k=None: [it for it in items if it['s'] == s and (k is None or it['kind'] == k)]
    # header texts
    ty = vy or 1e9
    tx = []
    for x in o['texts']:
        if 250 < x['y'] < ty:
            tx += [l.strip() for l in x['t'].replace('\xa0', ' ').split('\n') if l.strip()]
    strap = tx[2] if len(tx) > 2 else ''
    cap = tx[4] if len(tx) > 4 else ''
    hero_imgs = sorted([it for it in by('header', 'image') if it['ids'] and it['w'] >= 400], key=lambda i: -i['w'])
    m = {'_help': HELP, 'year': Y, 'strapline': strap}
    m['hero'] = {'id': hid(hero_imgs[0]['ids'][0]), 'caption': cap} if hero_imgs else {}
    loc, cty = LOC.get(Y, ('', ''))
    m['venue'] = {'map_query': f'{loc}, {cty}' if cty and cty != loc else loc, 'map_zoom': 11, 'blurb': ''}
    capi = sorted([i for i in by('captains', 'image') if i['ids']], key=lambda i: (i['y'], i['x']))[:2]
    capi.sort(key=lambda i: i['x'])
    m['captains'] = {k: {'id': hid(c['ids'][0])} for k, c in zip(('BH', 'RT'), capi)} if len(capi) == 2 else {}
    acc = by('accommodation', 'gallery')
    m['accommodation'] = {'name': '', 'blurb': '', 'photos': [{'id': p['id'], 'caption': ''} for g in acc for p in g['items'] if re.fullmatch(r'[0-9a-f]{32}', str(p['id']))]}
    it_imgs = sorted([i for i in items if i['s'] == 'itinerary' and i['kind'] in ('image', 'slide') and i['ids']], key=lambda i: (i['y'], i['x']))
    m['itinerary_images'] = [{'id': hid(i['ids'][0]), 'caption': ''} for i in it_imgs]
    m['itinerary_extra'] = {}
    tp = sorted([i for i in by('teams', 'image') if i['ids']], key=lambda i: (i['y'], i['x']))[:2]
    tp.sort(key=lambda i: i['x'])
    m['team_photos'] = {k: hid(t['ids'][0]) for k, t in zip(('BH', 'RT'), tp)} if len(tp) == 2 else {}
    m['team_announcement'] = [vid(v) for v in by('announcement', 'video') + by('teams', 'video') if v.get('vimeo')]
    m['rc_images'] = []
    m['leaderboard_images'] = [f'boards/BDT_{Y}_Leaderboard_{n}.jpg' for n in range(1, 5) if os.path.exists(os.path.join(TM, 'boards', f'BDT_{Y}_Leaderboard_{n}.jpg'))]
    sb = [i for i in by('summary', 'image') if i['ids']]
    link = next((l['href'] for l in o.get('links', []) if l['s'] == 'summary' and '/post/' in l['href']), '') or \
        next((i['link'] for i in sb if '/post/' in (i.get('link') or '')), '')
    m['summary'] = {'banner': hid(sb[0]['ids'][0]) if sb else '', 'title': '', 'text': '', 'link': link}
    vs = []
    for key, title in (('slideshow', 'Photo Slideshow'), ('videos', 'Tour clips'), ('trophies', 'Trophy presentations')):
        v = [vid(x) for x in by(key, 'video') if x.get('vimeo')]
        if v:
            vs.append({'title': title, 'items': v})
    m['video_sections'] = vs
    m['gallery'] = [p['id'] for g in by('photos', 'gallery') for p in g['items'] if re.fullmatch(r'[0-9a-f]{32}', str(p['id']))]
    return m


if __name__ == '__main__':
    years = sys.argv[1:] or [y for y in A if y != '2024']
    for y in years:
        m = build(y, A[y])
        fp = os.path.join(TM, f'{y}.json')
        if os.path.exists(fp):  # keep any hand-written extras
            old = json.load(open(fp, encoding='utf-8'))
            for k in ('fact', 'fact_type', 'gallery_placeholder', 'header_photo'):
                if k in old: m[k] = old[k]
            for k in ('name', 'blurb', 'where', 'facts'):
                if old.get('accommodation', {}).get(k): m['accommodation'][k] = old['accommodation'][k]
            for k in ('title', 'text'):
                if old.get('summary', {}).get(k): m['summary'][k] = old['summary'][k]
        json.dump(m, open(fp, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
        print(y, 'hero', bool(m['hero']), 'caps', len(m['captains']), 'acc', len(m['accommodation']['photos']), 'itin', len(m['itinerary_images']),
              'teams', len(m['team_photos']), 'ann', len(m['team_announcement']), 'lb', len(m['leaderboard_images']),
              'vids', [len(s['items']) for s in m['video_sections']], 'gal', len(m['gallery']), 'link', bool(m['summary']['link']), '|', m['strapline'], '|', m['hero'].get('caption'))
