#!/usr/bin/env python3
"""Adds (or refreshes) the guard at the top of every site page:
  - <meta name="robots" content="noindex, nofollow"> so search engines don't list the GitHub copies;
  - a small script that keeps the mouse wheel inside the page and styles its scroll bars when it is shown inside the Wix page, and,
    when a page is opened on its own (not inside bigdogstour.com, and not in the BDT app,
    which loads the pages directly and marks itself "BDTApp"), stops it and shows a short note instead.
The phone results page (scorer.html) only gets the noindex tag, since it is opened directly on a phone.
    python3 tools/page_guard.py            (run from the repository folder; safe to run again)"""
import glob, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
META = '<meta name="robots" content="noindex, nofollow">'
NOTE = ('<head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">' + META +
        '<title>Big Dogs Tour</title></head><body style="margin:0;min-height:100vh;display:flex;align-items:center;'
        'justify-content:center;background:#050B09;color:#F4F1E4;font:16px/1.5 system-ui,sans-serif;text-align:center;'
        'padding:24px;box-sizing:border-box"><p>This page is part of the Big Dogs Tour website.<br>'
        '<a style="color:#F0C566" href="https://www.bigdogstour.com">Go to www.bigdogstour.com</a></p></body>')
# Inside the Wix page: once the page's own scroll reaches the top or bottom, stop the mouse wheel or finger
# carrying on into the Wix page around it (only while the page is taller than its box, so a short page still
# lets the Wix page scroll).
# ...and gives its scroll bars the site's dark and gold look, so the box doesn't look like a separate window.
BARS = ('html{scrollbar-width:thin;scrollbar-color:#C9A24A #0B1410}'
        '::-webkit-scrollbar{width:10px;height:10px}::-webkit-scrollbar-track,::-webkit-scrollbar-corner{background:#0B1410}'
        '::-webkit-scrollbar-thumb{background:#C9A24A;border-radius:6px;border:2px solid #0B1410}'
        '::-webkit-scrollbar-thumb:hover{background:#F0C566}')
CONTAIN = ("if(!alone){var st=document.createElement('style');st.id='bdt-bars';st.textContent='" + BARS + "';"
           "(document.head||document.documentElement).appendChild(st);"
           "var f=function(){var d=document.documentElement,b=document.body,"
           "v=d.scrollHeight>innerHeight+2?'contain':'';d.style.overscrollBehaviorY=v;if(b)b.style.overscrollBehaviorY=v};"
           "addEventListener('load',f);addEventListener('resize',f);document.addEventListener('DOMContentLoaded',"
           "function(){(document.head||document.documentElement).appendChild(st);f();try{new ResizeObserver(f).observe(document.body)}catch(e){}});return}")
GUARD = ('<script id="bdt-guard">(function(){var alone;try{alone=window.top===window.self}catch(e){alone=false}' +
         CONTAIN +
         "if(/BDTApp/.test(navigator.userAgent)||location.protocol==='file:'||"
         "/^(localhost|127\\.|\\[::1\\])/.test(location.hostname))return;"
         "try{window.stop()}catch(e){}document.documentElement.innerHTML='" + NOTE.replace("'", "\\'").replace('<', '\\x3c') +
         "';})();</script>")  # no literal tags inside the script, so builders looking for <title> or <head> aren't confused
BLOCK = re.compile(r'<meta name="robots" content="noindex, nofollow">(<script id="bdt-guard">.*?</script>)?', re.S)
SKIP_GUARD = {'scorer.html'}
TEMPLATES = ['tour_page_template.html', 'tours_page_template.html', 'home_template.html', 'history_template.html']


def guard(s, name):
    s = BLOCK.sub('', s)
    add = META + ('' if name in SKIP_GUARD else GUARD)
    m = re.search(r'<head(\s[^>]*)?>', s, re.I)   # not <header>
    if m:
        return s[:m.end()] + add + s[m.end():]
    m = re.search(r'<meta charset[^>]*>', s, re.I)
    if m:
        return s[:m.end()] + add + s[m.end():]
    return add + s                       # page fragments with no <head> (team pages)


def main():
    files = sorted(set(glob.glob(os.path.join(ROOT, '*.html'))) |
                   {os.path.join(ROOT, t) for t in TEMPLATES if os.path.exists(os.path.join(ROOT, t))})
    for f in files:
        s = open(f, encoding='utf-8').read()
        new = guard(s, os.path.basename(f))
        if new != s:
            open(f, 'w', encoding='utf-8').write(new)
            print('guarded', os.path.basename(f))


if __name__ == '__main__':
    main()
