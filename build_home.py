"""Builds bdt_home.html (Home page embed) from home_template.html using the Master Playbook + courses data.
   python3 home/build_home.py [--preview]   (--preview inlines a local copy of the hero photo for testing)"""
import os, sys, json, csv, base64
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT); sys.path.insert(0, HERE)
import header_themes as HT, facts, header_a
D = HT._courses(); wb = HT._wb(); H = facts.load(wb)
T = sorted(D['tours'], key=lambda t: t['y'])
res = list(csv.DictReader(open(os.path.join(HT.SRC, 'bdt_team_results.csv'), encoding='utf-8-sig')))
cnt = {k: sum(1 for r in res if r['result'] == k) for k in ('Bloodhounds', 'Retrievers', 'Halved')}
last = res[-1]; LY = int(last['year']); lt = next(t for t in T if t['y'] == LY)
players = {p for y in H['sheets'] for p in H['sheets'][y]} | {x['p'] for y in H['ind'] for x in H['ind'][y]}
rounds = sum(len([s for s in x['r'] if s]) for y in H['ind'] for x in H['ind'][y])
courses = len({r['c'] for t in T for r in t['rounds']})
nums = [(len(T), 'Tours'), (len({t['cty'] for t in T}), 'Countries'), (courses, 'Courses played'), (len(players), 'Big Dogs'), (f'{rounds:,}', 'Rounds played')]
res_line = (f"<b>{last['result']}</b> won {last[last['result'].lower()]}–{last['bloodhounds' if last['result']=='Retrievers' else 'retrievers']}"
            if last['result'] != 'Halved' else f"Cup halved {last['bloodhounds']}–{last['retrievers']}") + f" · {last['courses']}"
hold = {k: sum(1 for r in res if r['cup_holders'] == k) for k in ('Bloodhounds', 'Retrievers')}
ret = {k: sum(1 for r in res if r['cup_holders'] == k and r['result'] == 'Halved') for k in ('Bloodhounds', 'Retrievers')}
dots = ''.join(f'<i class="{"b" if r["cup_holders"] == "Bloodhounds" else "r"}{" hv" if r["result"] == "Halved" else ""}" title="{r["year"]} · {r["note"]}"></i>' for r in res)
RCT = open(os.path.join(ROOT, 'options', 'rc_trophy_icon.b64')).read().strip()
LINKS = json.load(open(os.path.join(HERE, 'links.json')))
tiles = ''.join(f'<a class="tile {c}" href="{LINKS.get(k, "/")}" target="_top"><b>{k}</b><span>{d}</span></a>' for k, d, c in [
    ('Next Tour', 'BDT 2027 – Mallorca, 28 Apr–2 May', 'nx'), ('Tours', 'Every tour since 2002', ''), ('Bloodhounds', 'The red team', 'bh'), ('Retrievers', 'The blue team', 'rt'),
    ('Statistics', 'Records & numbers', ''), ('Trophies', 'Who won what', ''), ('Courses', 'Every course played', ''),
    ('Trivia', 'Facts & figures', ''), ('Handicaps', 'Current & past', ''), ('Dog Spots', 'Where we have been', ''),
    ('History', 'How it all began', ''), ('Nicknames', 'Every tour nickname', ''), ('Videos', 'Previews & reviews', ''),
    ('Rules', 'Rules, privacy & support', ''), ('Blog', 'Tour tales', '')])
hero = header_a.wix('588d17_b6f48a353ae74dedb7539d953634a626~mv2.jpg', 2044, 1012)
if '--preview' in sys.argv:
    hero = 'data:image/jpeg;base64,' + base64.b64encode(open('/mnt/user-data/uploads/Downloads/home_b6f48a35.jpg', 'rb').read()).decode()
rep = {'HERO': hero, 'CREST': open(os.path.join(HERE, 'crest.txt')).read(), 'TOURS': len(T), 'COUNTRIES': len({t['cty'] for t in T}),
       'BH': cnt['Bloodhounds'], 'RT': cnt['Retrievers'], 'H': cnt['Halved'], 'CUPS': len(res), 'HOLDERS': last['cup_holders'],
       'LY': LY, 'LLOC': f"{lt['loc']}", 'LRES': res_line, 'LLINK': LINKS.get(str(LY), '/tours'),
       'HB': hold['Bloodhounds'], 'HR': hold['Retrievers'], 'RB': ret['Bloodhounds'], 'RR': ret['Retrievers'], 'WB': cnt['Bloodhounds'], 'WR': cnt['Retrievers'], 'DOTS': dots, 'RCT': RCT, 'Y0': res[0]['year'], 'HCOL': '#ff5a5a' if last['cup_holders']=='Bloodhounds' else '#7d8fff',
       'NUMS': ''.join(f'<div><b>{a}</b><i>{b}</i></div>' for a, b in nums), 'TILES': tiles}
import variants
V = next((a.split('=')[1] for a in sys.argv if a.startswith('--variant=')), 'a')
h = open(os.path.join(HERE, 'home_template.html'), encoding='utf-8').read()
h = h.replace('{{HEROBLOCK}}', open(os.path.join(HERE, f'hero_{V}.html'), encoding='utf-8').read()).replace('{{VARCSS}}', variants.CSS[V])
for k, v in rep.items():
    h = h.replace('{{' + k + '}}', str(v))
out = os.path.join(ROOT, f'bdt_home_preview_{V}.html' if '--preview' in sys.argv else 'bdt_home.html')
open(out, 'w', encoding='utf-8').write(h); print('wrote', out, len(h) // 1024, 'KB', nums, cnt)
