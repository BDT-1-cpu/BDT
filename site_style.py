"""Shared tab look for the non-tour pages, so their buttons match the tour-page tabs (Oct 2026).
Also the team-page tweak that folds the section intro into the header."""
import re

TABS_CSS = """<style id="bdt-tabs-css">
#tabs>button,.subpage-tab,#chips>button{font:600 12.5px/1.15 Archivo,system-ui,sans-serif !important;letter-spacing:.02em !important;text-transform:none !important;
 border-radius:11px !important;border:1px solid rgba(240,197,102,.22) !important;background:#0f2219 !important;color:#E6ECE7 !important;padding:9px 14px !important;box-shadow:none !important;transition:border-color .15s,background .15s}
#tabs>button:hover,.subpage-tab:hover,#chips>button:hover{border-color:rgba(240,197,102,.55) !important}
#tabs>button.on,#tabs>button.active,.subpage-tab.active,.subpage-tab.on,#chips>button.on,#chips>button.active{background:linear-gradient(100deg,#F0C566,#C99A3D) !important;color:#14210F !important;border-color:#F0C566 !important}
#chips>button span,#chips>button b{color:inherit !important;opacity:.75}
</style>"""

TEAM_CSS = """<style id="bdt-team-css">
.page>.section-head{display:none !important}
.subpage-tabs:has(>:only-child){display:none !important}
.editions-wrap>.landing-heading:first-child{display:none !important}
.bdt-hero .bdt-hin>div{position:relative}
.bdt-hero .bdt-note{position:absolute;left:0;top:100%;width:max-content;max-width:min(640px,100%)}
@media(max-width:760px){.bdt-hero .bdt-hin{padding-bottom:60px !important}.bdt-hero .bdt-note{width:auto;right:0;max-width:none}}
</style>"""


def _put(html, block):
    sid = re.search(r'id="([^"]+)"', block).group(1)
    pat = re.compile(r'<style id="%s">.*?</style>' % re.escape(sid), re.S)
    if pat.search(html):
        return pat.sub(lambda m: block, html, count=1)
    if '</head>' in html:
        return html.replace('</head>', block + '</head>', 1)
    i = html.find('<style id="bdt-hero-css">')
    return html[:i] + block + html[i:] if i >= 0 else block + html


def apply_tabs(html):
    return _put(html, TABS_CSS)


def apply_team(html, note):
    html = _put(html, TEAM_CSS)
    if 'class="bdt-note"' not in html:
        html = re.sub(r'(<header class="bdt-hero[^>]*>.*?<div class="bdt-t2">.*?</div>)', lambda m: m.group(1) + f'<div class="bdt-note">{note}</div>', html, count=1, flags=re.S)
    return html


# ---------------------------------------------------------------- dark look for the formerly light pages (Oct 2026)
DARK_VARS = (":root{--ink:#F4F1E4;--muted:#A9BAAE;--bg:#050B09;--card:#10261c;--line:rgba(240,197,102,.16);"
             "--navy:#5068f2;--red:#ff2a2a;--g9:#F0C566;--g7:#c9a24a}")
DARK_BASE = """
body{background:radial-gradient(1100px 620px at 14% -8%,rgba(240,197,102,.08),transparent 60%),linear-gradient(160deg,#0a1a13,#050B09 60%) !important;background-color:#050B09 !important;color:var(--ink)}
select,input[type=search],input[type=text]{background:#0f2219 !important;color:#E6ECE7 !important;border-color:rgba(240,197,102,.22) !important}
#toTabs{background:#F0C566 !important;color:#14210F !important}
[style*="background:#fff"],[style*="background: #fff"],[style*="background:#f1f0ec"],[style*="background:#faf9f5"]{background:#10261c !important}
"""
_SKIP = ('.lb', '.tip', '.board', '.kyear', '.khead', '.kyr', 'bdt-', '#toTabs', '.thbg', 'svg', ':root', 'html', 'body')


def _lum(c):
    c = c.strip().lower()
    if c in ('white', '#fff', '#ffffff'):
        return 1.0
    if c in ('black',):
        return 0.0
    m = re.fullmatch(r'#([0-9a-f]{3}|[0-9a-f]{6})', c)
    if not m:
        return None
    h = m.group(1)
    if len(h) == 3:
        h = ''.join(x * 2 for x in h)
    r, g, b = (int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def dark_css(html):
    css = ' '.join(re.findall(r'<style(?![^>]*id="bdt-)[^>]*>(.*?)</style>', html, re.S))
    css = re.sub(r'/\*.*?\*/', '', css, flags=re.S)
    out = []
    for sel, body in re.findall(r'([^{}@]+)\{([^{}]*)\}', css):
        sel = sel.strip()
        if not sel or any(k in sel for k in _SKIP) or sel.startswith(('from', 'to', '0%', '100%')):
            continue
        decl = dict((k.strip().lower(), v.strip()) for k, v in (d.split(':', 1) for d in body.split(';') if ':' in d))
        new = {}
        bgv = decl.get('background-color') or decl.get('background') or ''
        bgcol = re.fullmatch(r'\s*(#[0-9a-fA-F]{3,6}|white)\s*', bgv)
        bg_l = _lum(bgcol.group(1)) if bgcol else None
        strong_bg = bool(bgv) and (bg_l is None or bg_l < .75) and 'var(--card)' not in bgv and 'var(--bg)' not in bgv
        if 'var(--ink)' in bgv:  # selected buttons etc: ink becomes light, so make them gold
            new['background'] = 'linear-gradient(100deg,#F0C566,#C99A3D)'
            new['color'] = '#14210F'
            if 'border-color' in decl:
                new['border-color'] = '#F0C566'
        elif bg_l is not None:
            if bg_l > .85:
                new['background' if 'background' in decl else 'background-color'] = '#10261c'
            elif bg_l > .6:
                new['background' if 'background' in decl else 'background-color'] = 'rgba(255,255,255,.08)'
        col = decl.get('color')
        if col and 'color' not in new:
            l = _lum(col)
            if l is not None and not (strong_bg and bg_l is not None and bg_l < .6) and not (strong_bg and bg_l is None):
                if l < .25:
                    new['color'] = '#E6ECE7'
                elif l < .6:
                    new['color'] = '#A9BAAE'
        for k in ('border', 'border-color', 'border-top', 'border-bottom'):
            v = decl.get(k)
            if v:
                m = re.search(r'#[0-9a-fA-F]{3,6}\b', v)
                if m and (_lum(m.group(0)) or 0) > .6:
                    new[k] = v.replace(m.group(0), 'rgba(240,197,102,.2)')
        if new:
            out.append(sel + '{' + ';'.join(f'{k}:{v} !important' for k, v in new.items()) + '}')
    return '<style id="bdt-dark-css">' + DARK_VARS + DARK_BASE + '\n'.join(out) + '</style>'


def apply_dark(html):
    return _put(html, dark_css(html))
