CSS = {
'a': """@media(max-width:760px){.hero{display:block;min-height:0;background:var(--bg)}
 .hero img.ph{position:relative;display:block;height:300px;object-position:60% 50%}
 .hero::after{background:linear-gradient(180deg,rgba(5,11,9,0) 150px,var(--bg) 300px)}.hin{margin-top:-64px}}""",
'b': """.heroB{background:var(--bg)}.heroB img.ph{display:block;width:100%;height:auto;max-height:640px;object-fit:cover;object-position:50% 60%}
 .heroB .tb{display:flex;align-items:center;justify-content:center;gap:24px;padding:26px 24px 30px;margin-top:-1px;background:linear-gradient(180deg,#120f1d,var(--bg))}
 .heroB h1{text-align:left}
 @media(max-width:760px){.heroB img.ph{max-height:none}.heroB .tb{flex-direction:column;text-align:center;gap:8px;padding:18px 14px 22px}.heroB h1,.heroB .tb>div{text-align:center}.crest{width:78px}.kick{font-size:11px}}""",
'c': """.heroC{position:relative;overflow:hidden;padding:46px 20px 40px;text-align:center;background:radial-gradient(700px 360px at 50% 0%,rgba(240,197,102,.16),transparent 70%),linear-gradient(160deg,#0A1C16,#050B09 75%)}
 .heroC .wm{position:absolute;right:-90px;top:-60px;width:420px;opacity:.07;filter:grayscale(1)}
 .heroC .tc{position:relative}.heroC .crest{width:150px;display:block;margin:0 auto 14px}
 .tribute{display:block;margin-top:26px;border:1px solid var(--line);border-radius:18px;overflow:hidden;background:var(--card)}
 .tribute img{display:block;width:100%;height:auto;max-height:520px;object-fit:cover;object-position:50% 60%}
 .tribute div{padding:24px;display:flex;flex-direction:column;justify-content:center}.tribute b{font:14px Anton,Impact,sans-serif;letter-spacing:.18em;color:var(--gold)}
 .tribute p{margin:8px 0 0;color:var(--soft)}.memo{display:none}
 @media(max-width:760px){.heroC{padding:30px 14px 28px}.heroC .crest{width:96px}.kick{font-size:11px}}""",
}
