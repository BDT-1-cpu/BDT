"""Adds the four timeline layouts to History.html as switchable views.

Run from the repository root:  python3 tools/build_history.py
Re-running replaces the previously added block, so it is safe to run again
after editing History.html or any bdt_timeline_*.html file.
"""
import json, re

LAYOUTS = [  # (key, tab label, source file)
    ('almanac', 'Almanac', 'bdt_timeline_almanac.html'),
    ('board', 'Roll of Honour', 'bdt_timeline_board.html'),
    ('fairway', 'Long Fairway', 'bdt_timeline_fairway.html'),
    ('stories', 'Tour Stories', 'bdt_timeline_stories.html'),
]
START, END = '<!--BDT-LAYOUTS-->', '<!--/BDT-LAYOUTS-->'

page = open('History.html', encoding='utf-8').read()
page = re.sub(re.escape(START) + '.*?' + re.escape(END) + r'\n?', '', page, flags=re.S)

data = None
templates = []
for key, label, src in LAYOUTS:
    s = open(src, encoding='utf-8').read()
    m = re.search(r'^const Y=(.*?);?\s*$', s, re.M)
    if data is None:
        data = m.group(1)
    assert m.group(1) == data, src + ' has different timeline data'
    s = s[:m.start()] + 'const Y=parent.__TLY;' + s[m.end():]
    templates.append(f'<script type="text/plain" id="tpl-{key}">' + s.replace('</script', '<\\/script') + '</script>')

tabs = '<button data-k="moments" class="on">Moments</button>' + ''.join(
    f'<button data-k="{k}">{label}</button>' for k, label, _ in LAYOUTS)

block = START + r'''
<style>
#tabs{display:flex;flex-wrap:wrap;justify-content:center;gap:8px;max-width:1100px;margin:22px auto 0;padding:0 14px}
#tlv{display:none;max-width:1240px;margin:16px auto 40px;padding:0 10px}
#tlv iframe{display:block;width:100%;border:0;background:#050B09}
</style>
<script>window.__TLY=''' + data + r''';
(function(){
const main=document.querySelector('main.wrap'),box=document.getElementById('tlv'),bar=document.getElementById('tabs');
const KID_CSS='.bdt-hero{display:none!important}html,body{overscroll-behavior:auto!important}';
const LB_CSS='.lbx{position:absolute!important;inset:auto 0 auto 0!important}';
let fr=null,ro=null,mo=null;
function pick(k){
 bar.querySelectorAll('button').forEach(b=>b.classList.toggle('on',b.dataset.k===k));
 if(ro)ro.disconnect();if(mo)mo.disconnect();if(fr){fr.remove();fr=null}
 if(k==='moments'){main.style.display='';box.style.display='none';return}
 main.style.display='none';box.style.display='block';
 const stories=k==='stories',phone=matchMedia('(max-width:760px)').matches;
 fr=document.createElement('iframe');fr.title=bar.querySelector('[data-k="'+k+'"]').textContent;fr.setAttribute('scrolling','no');
 fr.style.height=stories?(phone?'680px':'880px'):'1400px';
 const f=fr;
 f.onload=()=>{const d=f.contentDocument;if(!d)return;const st=d.createElement('style');st.textContent=KID_CSS+(stories?'':LB_CSS);d.head.appendChild(st);
  if(stories)return;
  const fit=()=>{const w=d.defaultView;let h=0;for(const c of d.body.children){const cs=w.getComputedStyle(c);if(cs.display==='none'||cs.position==='fixed'||cs.position==='absolute')continue;h=Math.max(h,c.getBoundingClientRect().bottom+w.scrollY+(parseFloat(cs.marginBottom)||0))}if(h)f.style.height=Math.ceil(h+parseFloat(w.getComputedStyle(d.body).paddingBottom||0)+8)+'px'};
  ro=new ResizeObserver(fit);ro.observe(d.body);fit();
  // a tall frame would centre its photo viewer off screen: keep it over the part of the page on screen
  mo=new MutationObserver(()=>{const lb=d.querySelector('.lbx.on');if(!lb)return;const r=f.getBoundingClientRect();
   lb.style.top=Math.max(0,-r.top)+'px';lb.style.height=Math.min(innerHeight,r.height)+'px'});
  mo.observe(d.body,{subtree:true,attributes:true,attributeFilter:['class']})};
 fr.srcdoc=document.getElementById('tpl-'+k).textContent.replace(/<\\\/script/g,'</script');
 box.appendChild(fr);
}
bar.addEventListener('click',e=>{const b=e.target.closest('button');if(b)pick(b.dataset.k)});
})();
</script>
''' + '\n'.join(templates) + '\n' + END

page = page.replace('<main class="wrap">', START + '<div class="tabs" id="tabs">' + tabs + '</div><div id="tlv"></div>' + END + '\n<main class="wrap">', 1)
page = page.replace('</body></html>', block + '\n</body></html>', 1)
open('History.html', 'w', encoding='utf-8').write(page)
print('History.html: added', ', '.join(l for _, l, _ in LAYOUTS))
