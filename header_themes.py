"""Option C headings: the Option A heading (header_a) with a background themed to the page's subject
instead of a photo.  This is the house style for every new BDT page – pick a theme key or add a new one.

    import header_themes
    html = header_themes.apply(html, 'Statistics', 'statistics')

Themes that use numbers read them from the Master Playbook each time, so they stay current.
"""
import json, os, re, html as _h
import header_a

HERE = os.path.dirname(os.path.abspath(__file__))
_parent = os.path.dirname(HERE)
SRC = os.environ.get('BDT_SRC') or (_parent if os.path.exists(os.path.join(_parent, 'Big Dogs Tour - Master Playbook.xlsx'))
                                    else '/mnt/user-data/uploads/Claude Workings For New Webpages')


def _wb():
    import openpyxl
    return openpyxl.load_workbook(os.path.join(SRC, 'Big Dogs Tour - Master Playbook.xlsx'), data_only=True, read_only=True)


def _courses():
    cs = open(os.path.join(SRC, 'bdt_tour_courses.html'), encoding='utf-8').read()
    return json.JSONDecoder().raw_decode(cs[cs.find('const D=') + 8:])[0]


# ------------------------------------------------------------------ backgrounds
def bg_statistics():
    import facts
    R = facts.load(_wb())['res']
    ys = sorted(R); n = len(ys); W = 1000; bw = W / n; out = []
    for i, y in enumerate(ys):
        d = R[y]['bh'] - R[y]['rt']; hh = min(abs(d), 11) / 11 * 120 + 6
        x = i * bw + bw * .18; w = bw * .64
        if R[y]['w'] == 'H' or d == 0:
            out.append(f'<rect x="{x:.1f}" y="146" width="{w:.1f}" height="8" rx="3" fill="#F0C566" opacity=".75"/>')
        elif d > 0:
            out.append(f'<rect x="{x:.1f}" y="{150 - hh:.1f}" width="{w:.1f}" height="{hh:.1f}" rx="3" fill="#ff2a2a" opacity=".75"/>')
        else:
            out.append(f'<rect x="{x:.1f}" y="150" width="{w:.1f}" height="{hh:.1f}" rx="3" fill="#4d63ff" opacity=".8"/>')
        out.append(f'<text x="{x + w / 2:.1f}" y="290" font-size="11" fill="#F0C566" opacity=".35" text-anchor="middle" font-family="Anton,Impact">{str(y)[2:]}</text>')
    grid = ''.join(f'<line x1="0" x2="{W}" y1="{y}" y2="{y}" stroke="#F0C566" stroke-opacity=".07"/>' for y in range(30, 280, 30))
    return (f'<svg class="bgsvg" viewBox="0 0 {W} 300" preserveAspectRatio="none">{grid}'
            f'<line x1="0" x2="{W}" y1="150" y2="150" stroke="#F0C566" stroke-opacity=".35"/>{"".join(out)}</svg>')


def bg_trophies():
    ts = open(os.path.join(SRC, 'bdt_trophies.html'), encoding='utf-8').read()
    big = dict(re.findall(r"label:\s*'([^']+)',\s*img:\s*'(data:image/[a-z]+;base64,[A-Za-z0-9+/=]+)'", ts))
    order = ['Shitzu', 'Great Dane', 'Rottweiler', '2nd', 'Big Dogs Ryder Cup', 'Green Jacket', '3rd', 'Poodle', 'St Bernard', 'Goblat']
    return '<div class="trow">' + ''.join(f'<img src="{big[k]}" alt="">' for k in order if k in big) + '</div>'


def bg_courses():
    D = _courses()
    ids = [r['t'] for t in sorted(D['tours'], key=lambda t: -t['y']) for r in t['rounds'] if r.get('t')][:27]
    return '<div class="mos">' + ''.join(f'<span><img src="{header_a.wix(i, 320, 200)}" alt="" loading="lazy"></span>' for i in ids) + '</div>'


def bg_facts():
    import facts
    wb = _wb(); H = facts.load(wb); D = _courses()
    players = {p for y in H['sheets'] for p in H['sheets'][y]}
    matches = sum(1 for r in list(wb['RC Matches'].iter_rows(values_only=True))[1:] if r[0] and r[10] != 'Abandoned')
    rounds = sum(len([s for s in x['r'] if s]) for y in H['ind'] for x in H['ind'][y])
    courses = len({r['c'] for t in D['tours'] for r in t['rounds']})
    items = [(len(D['tours']), 'tours'), (len({t['cty'] for t in D['tours']}), 'countries'), (matches, 'Ryder Cup matches'),
             (len(players), 'Big Dogs'), (courses, 'courses'), (rounds, 'rounds played')]
    return '<div class="nums">' + ''.join(f'<span><b>{a:,}</b><i>{b}</i></span>' for a, b in items) + '</div>'


def bg_handicaps():
    par = [4, 5, 3, 4, 4, 4, 3, 5, 4, 4, 4, 3, 5, 4, 4, 3, 4, 5]
    si = [7, 3, 15, 11, 1, 9, 17, 5, 13, 8, 2, 16, 4, 12, 10, 18, 14, 6]
    row = lambda lab, v: f'<tr><th>{lab}</th>' + ''.join(f'<td>{x}</td>' for x in v) + '</tr>'
    return ('<table class="scard">' + row('Hole', range(1, 19)) + row('Par', par) + row('S.I.', si) +
            row('Shots', [1 if s <= 14 else '' for s in si]) + row('Pts', [2, 3, 1, 2, 3, 2, 0, 3, 2, 2, 3, 1, 2, 2, 3, 2, 2, 4]) + '</table>')


def bg_dogspots():
    return '<div class="paws"></div>'


def bg_history():
    """A timeline strip of every tour year behind the heading."""
    ys = [t['y'] for t in sorted(_courses()['tours'], key=lambda t: t['y'])]
    W = 1000; n = len(ys); out = ['<line x1="0" x2="1000" y1="150" y2="150" stroke="#F0C566" stroke-opacity=".35" stroke-width="2"/>']
    for i, y in enumerate(ys):
        x = 30 + i * (W - 60) / max(1, n - 1)
        up = i % 2 == 0
        out.append(f'<circle cx="{x:.1f}" cy="150" r="5" fill="#F0C566" fill-opacity=".45"/>')
        out.append(f'<line x1="{x:.1f}" x2="{x:.1f}" y1="150" y2="{110 if up else 190}" stroke="#F0C566" stroke-opacity=".2"/>')
        out.append(f'<text x="{x:.1f}" y="{100 if up else 214}" font-size="20" fill="none" stroke="#F0C566" stroke-opacity=".38" '
                   f'stroke-width=".9" text-anchor="middle" font-family="Anton,Impact">{y}</text>')
    return f'<svg class="bgsvg" viewBox="0 0 {W} 300" preserveAspectRatio="xMidYMid slice">{"".join(out)}</svg>'


THEMES = {'statistics': bg_statistics, 'trophies': bg_trophies, 'courses': bg_courses, 'facts': bg_facts,
          'handicaps': bg_handicaps, 'dogspots': bg_dogspots, 'history': bg_history}

PAW = ("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='120' height='120' viewBox='0 0 120 120'>"
       "<g fill='%23F0C566' fill-opacity='.13' transform='rotate(-18 60 60)'><ellipse cx='60' cy='72' rx='17' ry='14'/>"
       "<ellipse cx='40' cy='50' rx='7' ry='9'/><ellipse cx='53' cy='40' rx='7' ry='9'/><ellipse cx='67' cy='40' rx='7' ry='9'/>"
       "<ellipse cx='80' cy='50' rx='7' ry='9'/></g></svg>")

CSS = """<style id="bdt-hero-theme">
.bdt-hero.o-th{background-image:none}
.bdt-hero .thbg{position:absolute;inset:0;z-index:0;overflow:hidden;pointer-events:none}
.bdt-hero.o-th::before{z-index:1;background:linear-gradient(90deg,rgba(5,11,9,.92) 0%,rgba(5,11,9,.6) 45%,rgba(5,11,9,.2) 85%),linear-gradient(0deg,rgba(5,11,9,.85),transparent 55%)}
.bdt-hero.o-th .bdt-hin,.bdt-hero.o-th .bdt-stripe{z-index:2}
.bdt-hero.th-statistics{background:#06120d}.bdt-hero .bgsvg{position:absolute;left:0;right:0;top:8%;width:100%;height:92%}
.bdt-hero.th-trophies{background:#000}.bdt-hero.th-trophies .thbg{background:radial-gradient(ellipse 45% 70% at 68% 30%,rgba(240,197,102,.16),transparent 70%)}
.bdt-hero .trow{position:absolute;right:-2%;bottom:6%;left:28%;display:flex;align-items:flex-end;justify-content:center;gap:1.2%;height:84%}
.bdt-hero .trow img{height:62%;width:auto;mix-blend-mode:lighten;-webkit-mask-image:radial-gradient(ellipse 60% 62% at 50% 50%,#000 55%,transparent 100%);mask-image:radial-gradient(ellipse 60% 62% at 50% 50%,#000 55%,transparent 100%)}
.bdt-hero .trow img:nth-child(5),.bdt-hero .trow img:nth-child(6){height:96%}.bdt-hero .trow img:nth-child(4),.bdt-hero .trow img:nth-child(7){height:76%}
.bdt-hero .mos{position:absolute;inset:0;display:grid;grid-template-columns:repeat(9,1fr);grid-template-rows:repeat(3,1fr);gap:2px}
.bdt-hero .mos span{overflow:hidden;background:#0d2419}.bdt-hero .mos img{width:100%;height:100%;object-fit:cover;display:block;filter:saturate(.95) brightness(.85)}
.bdt-hero.th-facts{background:radial-gradient(ellipse at 80% 30%,#163626,#050B09 70%)}
.bdt-hero .nums{position:absolute;inset:-4% -4% 0 48%;display:flex;flex-wrap:wrap;align-content:center;gap:0 34px;transform:rotate(-6deg)}
.bdt-hero .nums span{display:flex;align-items:baseline;gap:8px;white-space:nowrap}
.bdt-hero .nums b{font:84px/1 Anton,Impact,sans-serif;color:transparent;-webkit-text-stroke:1.5px rgba(240,197,102,.32)}
.bdt-hero .nums i{font:700 13px Archivo,sans-serif;font-style:normal;letter-spacing:.14em;text-transform:uppercase;color:rgba(240,197,102,.32)}
.bdt-hero.th-handicaps{background:#0a1a13}
.bdt-hero .scard{position:absolute;right:-3%;top:10%;width:78%;border-collapse:collapse;transform:rotate(-4deg);font:600 15px Archivo,sans-serif;color:rgba(240,197,102,.35)}
.bdt-hero .scard th,.bdt-hero .scard td{border:1px solid rgba(240,197,102,.16);padding:7px 0;text-align:center}.bdt-hero .scard th{font:13px Anton,Impact,sans-serif;letter-spacing:.08em;width:56px;color:rgba(240,197,102,.35)}
.bdt-hero.th-dogspots{background:#081510}.bdt-hero.th-history{background:radial-gradient(ellipse at 70% 40%,#13301f,#050B09 70%)}.bdt-hero .paws{position:absolute;inset:0;background:url("PAW") 0 0/120px 120px repeat}
@media(max-width:600px){
 .bdt-hero.o-th::before{background:linear-gradient(0deg,rgba(5,11,9,.95),rgba(5,11,9,.5) 60%,rgba(5,11,9,.25))}
 .bdt-hero .trow{left:0;right:0;top:4%;bottom:auto;height:46%;gap:0}.bdt-hero .trow img{height:70%}.bdt-hero .trow img:nth-child(-n+2),.bdt-hero .trow img:nth-child(n+9){display:none}
 .bdt-hero .mos{grid-template-columns:repeat(4,1fr);grid-template-rows:repeat(4,1fr)}.bdt-hero .mos span:nth-child(n+17){display:none}
 .bdt-hero .nums{inset:-4% -30% 0 -10%}.bdt-hero .nums b{font-size:58px}
 .bdt-hero .scard{width:190%;right:-110%;top:6%}}
</style>""".replace('PAW', PAW)


def apply(html, sub, theme, title='Big Dogs Tour'):
    """Put the themed Option C heading on a page (replaces any earlier bdt-head / bdt-hero heading)."""
    html = header_a.apply(html, title, sub, '', extra_class=f'o-th th-{theme}', photo_style='')
    html = re.sub(r'<style id="bdt-hero-theme">.*?</style>', '', html, flags=re.S)
    html = re.sub(r'(<header class="bdt-hero o-th th-[a-z]+"\s*>)', lambda m: m.group(1) + f'<div class="thbg">{THEMES[theme]()}</div>', html, count=1)
    assert 'class="thbg"' in html
    i = html.find('</head>')
    if i == -1:
        i = html.find('<header class="bdt-hero')
    return html[:i] + CSS + html[i:]
