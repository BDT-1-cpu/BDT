"""Adds the four timeline layouts to History.html as switchable views, plus the 101 Greatest Tour Moments tab
(cards built from moments/moments.json; the PDFs and thumbnails in moments/ come from Claude's 101 Moments build).

Run from the repository root:  python3 tools/build_history.py
Re-running replaces the previously added block, so it is safe to run again
after editing History.html or any bdt_timeline_*.html file.
"""
import json, os, re

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

tabs = '<button data-k="moments" class="on">Tour Timeline</button>' + ''.join(
    f'<button data-k="{k}">{label}</button>' for k, label, _ in LAYOUTS) + '<button data-k="m101">101 Greatest</button>'

# 101 Greatest Tour Moments: one card per memory, each opening that memory's PDF (moments/, made by Claude's 101 Moments build)
M101 = json.load(open('moments/moments.json', encoding='utf-8'))
for m in M101.values():   # a new card photo gets a new address, so phones and browsers don't show the old one
    m['v'] = int(os.path.getmtime(f'moments/thumbs/{m["n"]}.jpg')) % 100000
# the whole book (the smaller sharing copy, ~79 MB) is too big for GitHub, so it lives in Wix Media Manager (History folder)
BOOK_URL = 'https://588d179a-797a-48bc-9036-1ad66c69fd17.usrfiles.com/ugd/588d17_bc3e3ca5ace84aaea63e1b67df3208c2.pdf'
BOOK_BTN = (f'<a class="m1book" href="{BOOK_URL}" target="_blank" rel="noopener">Download the whole book (PDF, 79 MB)</a>' if BOOK_URL else '')
M101_HTML = ('<div id="m101"><div class="m1intro"><h2>101 Greatest Tour Moments</h2>'
             '<p>The countdown of the 101 greatest moments in tour history, written for BDT 2026 in Scottsdale. '
             'Tap a memory to open it – the videos inside play on Vimeo or YouTube.</p>'
             '<div class="m1bar"><input id="m1q" type="search" placeholder="Search by title, Dog or year" aria-label="Search the memories">'
             '<button id="m1o" type="button">Show 1 → 101</button>' + BOOK_BTN + '</div></div>'
             '<div class="m1grid" id="m1g"></div><p class="m1none" id="m1n" hidden>No memories match that search.</p></div>')

block = START + r'''
<style>
#tabs{display:flex;flex-wrap:wrap;justify-content:center;gap:8px;max-width:1100px;margin:22px auto 0;padding:0 14px}
#tlv{display:none;max-width:1240px;margin:16px auto 40px;padding:0 10px}
#tlv iframe{display:block;width:100%;border:0;background:#050B09}
#m101{display:none;max-width:1100px;margin:16px auto 50px;padding:0 14px}
#m101 .m1intro{background:var(--card);border:1px solid var(--line);border-radius:18px;padding:18px 22px;margin-bottom:18px}
#m101 h2{font:26px/1.1 Anton,Impact,sans-serif;letter-spacing:.03em;color:var(--gold);margin:0 0 6px;text-transform:uppercase}
#m101 .m1intro p{margin:0;color:var(--soft)}
#m101 .m1bar{display:flex;flex-wrap:wrap;gap:10px;margin-top:14px}
#m1q{flex:1 1 220px;min-width:0;font:15px Archivo,system-ui,sans-serif;color:var(--ink);background:#0b1914;border:1px solid var(--line);border-radius:11px;padding:9px 12px}
#m1q:focus{outline:none;border-color:var(--gold)}
.m1book{font:600 12.5px Archivo,system-ui,sans-serif;color:#14210F;background:linear-gradient(100deg,var(--gold),var(--gold2));border-radius:11px;padding:9px 14px;text-decoration:none;white-space:nowrap}
#m1o{font:600 12.5px Archivo,system-ui,sans-serif;color:var(--ink);background:#0f2219;border:1px solid rgba(240,197,102,.22);border-radius:11px;padding:9px 14px;cursor:pointer}
.m1grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(200px,1fr));gap:14px}
.m1c{display:flex;flex-direction:column;text-decoration:none;background:var(--card);border:1px solid var(--line);border-radius:14px;overflow:hidden;transition:border-color .15s,transform .15s}
.m1c:hover{border-color:var(--gold);transform:translateY(-2px)}
.m1ph{position:relative;aspect-ratio:4/3;background:#0b1914}
.m1c img{display:block;width:100%;height:100%;object-fit:cover}
.m1no{position:absolute;left:8px;bottom:6px;font:34px/1 Anton,Impact,sans-serif;color:var(--gold);text-shadow:0 2px 8px rgba(0,0,0,.85)}
.m1tx{padding:9px 12px 12px}
.m1c b{display:block;font-weight:700;line-height:1.25}
.m1c i{display:block;font-style:normal;font-size:12.5px;color:var(--soft);margin-top:3px}
.m1c small{display:block;font-size:11.5px;color:var(--dim);margin-top:4px}
.m1none{color:var(--soft);text-align:center}
@media(max-width:600px){.m1grid{grid-template-columns:repeat(2,minmax(0,1fr));gap:10px}.m1no{font-size:28px}.m1tx{padding:8px 9px 10px}.m1c b{font-size:14px}}
</style>
<script>window.__TLY=''' + data + r''';
(function(){
const main=document.querySelector('main.wrap'),box=document.getElementById('tlv'),bar=document.getElementById('tabs');
const KID_CSS='.bdt-hero{display:none!important}html,body{overscroll-behavior:auto!important}';
const LB_CSS='.lbx{position:absolute!important;inset:auto 0 auto 0!important}';
let fr=null,ro=null,mo=null;
const m101=document.getElementById('m101'),M1=''' + json.dumps(list(M101.values()), ensure_ascii=False) + r''';
let m1up=false;
function m1draw(){
 const q=document.getElementById('m1q').value.trim().toLowerCase(),g=document.getElementById('m1g');
 const esc=s=>String(s).replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
 const L=M1.filter(m=>!q||(m.n+' '+m.t+' '+m.d+' '+(m.y||'')).toLowerCase().includes(q)).sort((a,b)=>m1up?a.n-b.n:b.n-a.n);
 g.innerHTML=L.map(m=>`<a class="m1c" href="moments/${encodeURIComponent(m.f)}" target="_blank" rel="noopener"><div class="m1ph">${m.img?`<img src="moments/thumbs/${m.n}.jpg?v=${m.v}" alt="" loading="lazy">`:''}<span class="m1no">${m.n}</span></div><div class="m1tx"><b>${esc(m.t)}</b><i>${[/\d{4}/.test(m.y)?'BDT '+m.y:m.y&&m.y+' tours',m.d&&esc(m.d)].filter(Boolean).join(' · ')}</i><small>${m.p} page${m.p>1?'s':''} · PDF ${m.mb} MB</small></div></a>`).join('');
 document.getElementById('m1n').hidden=L.length>0;
}
document.getElementById('m1q').addEventListener('input',m1draw);
document.getElementById('m1o').addEventListener('click',e=>{m1up=!m1up;e.target.textContent=m1up?'Show 101 → 1':'Show 1 → 101';m1draw()});
function pick(k){
 bar.querySelectorAll('button').forEach(b=>b.classList.toggle('on',b.dataset.k===k));
 if(ro)ro.disconnect();if(mo)mo.disconnect();if(fr){fr.remove();fr=null}
 m101.style.display=k==='m101'?'block':'none';
 if(k==='m101'){main.style.display='none';box.style.display='none';m1draw();return}
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

page = page.replace('<main class="wrap">', START + '<div class="tabs" id="tabs">' + tabs + '</div><div id="tlv"></div>' + M101_HTML + END + '\n<main class="wrap">', 1)
page = page.replace('</body></html>', block + '\n</body></html>', 1)
open('History.html', 'w', encoding='utf-8').write(page)
print('History.html: added', ', '.join(l for _, l, _ in LAYOUTS))
