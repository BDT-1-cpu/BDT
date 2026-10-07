"""Option A 'statement photo' heading, shared by every new BDT page.
apply(html, title, sub, photo) swaps the old <header class="bdt-head">…</header> for the new one
(keeping the page's own crest <img>) and adds the CSS. Re-running on an already-converted page
replaces the previous version of the heading."""
import re

def wix(fname, w=1600, h=700):
    if not fname:
        return ''
    if fname.startswith('http') or fname.startswith('data:'):
        return fname
    if not fname.startswith('588d17_'):
        fname = '588d17_' + fname
    if '~' not in fname:
        fname += '~mv2.jpg'
    return f'https://static.wixstatic.com/media/{fname}/v1/fill/w_{w},h_{h},al_c,q_82,enc_auto/{fname}'

CSS = """<style id="bdt-hero-css">
@import url('https://fonts.googleapis.com/css2?family=Anton&display=swap');
.bdt-hero{position:relative;z-index:5;display:flex;align-items:center;min-height:300px;margin:0;padding:0;overflow:hidden;text-align:left;line-height:normal;letter-spacing:normal;background:#050B09 var(--hero,none) center 42%/cover no-repeat;box-sizing:border-box}
.bdt-hero::before{content:"";position:absolute;inset:0;background:linear-gradient(180deg,rgba(5,11,9,.12) 0%,rgba(5,11,9,.5) 45%,rgba(5,11,9,.96) 100%)}
.bdt-hero .bdt-hin{position:relative;display:flex;align-items:center;gap:22px;width:100%;max-width:1180px;margin:0 auto;padding:28px 32px 32px;box-sizing:border-box}
.bdt-hero .bdt-crest{width:110px;height:auto;flex:none;display:block;filter:drop-shadow(0 6px 18px rgba(0,0,0,.7))}
.bdt-hero .bdt-kicker{font:13px Anton,Impact,sans-serif;letter-spacing:.14em;text-shadow:0 1px 6px rgba(0,0,0,.7)}
.bdt-hero .bdt-kicker .bh{color:#FF2a2a}.bdt-hero .bdt-kicker .vs{color:#F0C566}.bdt-hero .bdt-kicker .rt{color:#5068f2}
.bdt-hero .bdt-t1{font:clamp(40px,7.4vw,84px)/.92 Anton,Impact,sans-serif;text-transform:uppercase;letter-spacing:.01em;margin:4px 0 0;background:linear-gradient(100deg,#FBF7E9 10%,#F0C566 55%,#FBF7E9 90%);-webkit-background-clip:text;background-clip:text;color:transparent;filter:drop-shadow(0 2px 10px rgba(0,0,0,.55))}
.bdt-hero .bdt-t2{font:clamp(16px,2.6vw,26px) Anton,Impact,sans-serif;letter-spacing:.12em;color:#F0C566;text-transform:uppercase;margin-top:8px;text-shadow:0 1px 8px rgba(0,0,0,.8)}
.bdt-hero .bdt-yr{white-space:nowrap}
.bdt-hero .bdt-stripe{position:absolute;left:0;right:0;bottom:0;height:4px;background:linear-gradient(90deg,#FF0000 0 50%,#5068f2 50%)}
@media(max-width:760px){.bdt-hero{min-height:210px}.bdt-hero .bdt-hin{flex-direction:row;align-items:center;gap:12px;padding:20px 12px 22px}.bdt-hero .bdt-crest{width:64px}.bdt-hero .bdt-kicker{font-size:9.5px;letter-spacing:.1em}.bdt-hero .bdt-t1{font-size:34px}.bdt-hero .bdt-t2{font-size:12px;letter-spacing:.08em;margin-top:6px}}
/* card layout to match the tour pages (Oct 2026) */
.bdt-hero img.bdt-crest:not([src]){visibility:hidden}
.bdt-hero .bdt-note{font:600 13px/1.35 Archivo,system-ui,sans-serif;color:#d6dfd8;margin-top:8px;text-shadow:0 1px 6px #000;max-width:640px}
@media(min-width:761px){
.bdt-hero{margin:10px auto 0;max-width:1180px;width:calc(100% - 36px);border-radius:20px;min-height:280px;box-shadow:0 0 0 1px rgba(255,255,255,.07),0 18px 40px -20px rgba(0,0,0,.9)}
.bdt-hero .bdt-hin{padding:24px 34px 28px;gap:26px;max-width:none}
.bdt-hero .bdt-crest{width:112px}
.bdt-hero .bdt-kicker{font-size:12px;letter-spacing:.16em}
.bdt-hero .bdt-t1{font-size:62px}
.bdt-hero .bdt-t2{font-size:17px;margin-top:8px}
.bdt-hero .bdt-note{font-size:14px;margin-top:10px}
}
@media(max-width:760px){
.bdt-hero{min-height:0;margin:10px 10px 0;border-radius:16px;border:1px solid rgba(240,197,102,.28);box-shadow:0 14px 34px -16px rgba(0,0,0,.9)}
.bdt-hero .bdt-hin{padding:16px 14px 18px;gap:12px}
.bdt-hero .bdt-crest{width:60px}
.bdt-hero .bdt-kicker{font-size:9px;letter-spacing:.09em}
.bdt-hero .bdt-t1{font-size:30px;line-height:.95}
.bdt-hero .bdt-t2{font-size:12px;margin-top:5px}
.bdt-hero .bdt-note{font-size:11.5px;margin-top:6px}
}
</style>"""

KICK = '<span class="bh">BLOODHOUNDS</span> <span class="vs">v</span> <span class="rt">RETRIEVERS</span>'


def header_html(crest_img, title, sub, photo, extra_class='', kicker=None):
    return (f'<header class="bdt-hero {extra_class}" style="--hero:url(\'{photo}\')"><div class="bdt-hin">{crest_img}'
            f'<div><div class="bdt-kicker">{kicker or KICK}</div>'
            f'<div class="bdt-t1">{title}</div><div class="bdt-t2">{sub}</div></div></div><div class="bdt-stripe"></div></header>')

def apply(html, title, sub, photo, extra_class='', photo_style=None, kicker=None):
    m = re.search(r'<header class="bdt-(?:head|hero)[^"]*"[^>]*>.*?</header>', html, re.S)
    if not m:
        raise ValueError('no BDT header found')
    old = m.group(0)
    crest = re.search(r'<img[^>]*class="bdt-crest"[^>]*>', old).group(0)
    crest = crest.replace(' loading="lazy"', '')
    new = header_html(crest, title, sub, photo, extra_class, kicker)
    if photo_style is not None:
        new = new.replace(f'style="--hero:url(\'{photo}\')"', photo_style)
    html = html[:m.start()] + new + html[m.end():]
    html = re.sub(r'<style id="bdt-hero-css">.*?</style>', '', html, flags=re.S)
    i = html.find('</head>')
    if i == -1:
        i = html.find('<header class="bdt-hero')
    return html[:i] + CSS + html[i:]
