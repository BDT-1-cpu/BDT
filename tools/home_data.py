"""Updates the figures on Home.html in place: the Ryder Cup panel (cups, wins, retentions, year-by-year
dots, holders), the Latest tour card, the numbers row and the "Est. 2002 · N tours · N countries" line.

Data: bdt_team_results.csv (one row per Ryder Cup), Courses.html's tour list and the Master Playbook.
Everything else on the page (layout, tiles, hand-finished wording) is left as it is."""
import html as H
import re
from update_site import norm


def update(page, book, courses, res, links):
    T = sorted(courses['tours'], key=lambda t: int(t['y']))
    hold = {k: sum(1 for r in res if r['cup_holders'] == k) for k in ('Bloodhounds', 'Retrievers')}
    ret = {k: sum(1 for r in res if r['cup_holders'] == k and r['result'] == 'Halved') for k in hold}
    win = {k: hold[k] - ret[k] for k in hold}
    last = res[-1]
    LY = int(last['year'])
    lt = next(t for t in T if int(t['y']) == LY)

    ind = [r for r in book.g['Individual'][1:] if isinstance(norm(r[0]), int)]
    rounds = sum(1 for r in ind for k in (2, 3, 4) if isinstance(norm(r[k]), (int, float)))
    # tours with no Stableford scores (2002-2005): everyone placed played every round, a missed cut one fewer
    played = {norm(r[0]): norm(r[2]) for r in book.g['Tours'][1:] if isinstance(norm(r[0]), int)}
    for y in sorted({norm(r[0]) for r in ind}):
        rows = [r for r in ind if norm(r[0]) == y]
        if any(isinstance(norm(r[k]), (int, float)) for r in rows for k in (2, 3, 4)):
            continue
        n = int(played.get(y) or 0)
        rounds += sum(n - 1 if str(norm(r[5])).upper() == 'MC' else n for r in rows)
    players = len([r for r in book.g['Players'][1:] if norm(r[0])])
    courses_n = len({o['k'] for t in T for o in t['rounds']})
    countries = len({t['cty'] for t in T})

    s = page

    def sub(pattern, repl, flags=0):
        nonlocal s
        s2, k = re.subn(pattern, repl, s, count=1, flags=flags)
        if k != 1:
            raise SystemExit(f'Home.html: could not find {pattern!r}')
        s = s2

    sub(r'(<span class="lab2">All-time · )\d+( cups since )\d+', rf'\g<1>{len(res)}\g<2>{res[0]["year"]}')
    sub(r'(<div class="side bh"><span class="s">)\d+(</span><b>Bloodhounds</b><small>)\d+ won · \d+ retained',
        rf'\g<1>{hold["Bloodhounds"]}\g<2>{win["Bloodhounds"]} won · {ret["Bloodhounds"]} retained')
    sub(r'(<div class="side rt"><span class="s">)\d+(</span><b>Retrievers</b><small>)\d+ won · \d+ retained',
        rf'\g<1>{hold["Retrievers"]}\g<2>{win["Retrievers"]} won · {ret["Retrievers"]} retained')

    # dots: keep each existing year's tooltip, add any new year from the results file
    m = re.search(r'(<div class="dots"[^>]*>)(.*?)(</div>)', s, re.S)
    old = dict(re.findall(r'title="(\d{4}) · ([^"]*)"', m.group(2)))
    dots = ''.join(
        f'<i class="{"b" if r["cup_holders"] == "Bloodhounds" else "r"}{" hv" if r["result"] == "Halved" else ""}" '
        f'title="{r["year"]} · {old.get(r["year"]) or H.escape(r["note"], quote=True)}"></i>' for r in res)
    s = s[:m.start(2)] + dots + s[m.end(2):]

    col = '#ff5a5a' if last['cup_holders'] == 'Bloodhounds' else '#7d8fff'
    sub(r'(<div class="holders"><span>Cup holders</span><b style="color:)[^"]*(">)[^<]*(</b>)',
        rf'\g<1>{col}\g<2>{last["cup_holders"]}\g<3>')

    if last['result'] != 'Halved':
        other = 'bloodhounds' if last['result'] == 'Retrievers' else 'retrievers'
        res_line = f"<b>{last['result']}</b> won {last[last['result'].lower()]}–{last[other]}"
    else:
        res_line = f"Cup halved {last['bloodhounds']}–{last['retrievers']}"
    res_line += f" · {last['courses']}"
    sub(r'(<div class="lab">Latest tour</div><div class="t">BDT )\d+ · [^<]*(</div>\s*<div class="w">).*?(</div></div><a class="btn" href=")[^"]*(" target="_top">See the )\d+( tour)',
        lambda mm: f'{mm.group(1)}{LY} · {lt["loc"]}{mm.group(2)}{res_line}{mm.group(3)}{links.get(str(LY), "/tours")}{mm.group(4)}{LY}{mm.group(5)}',
        re.S)

    nums = [(len(T), 'Tours'), (countries, 'Countries'), (courses_n, 'Courses played'), (players, 'Big Dogs'),
            (f'{rounds:,}', 'Rounds played')]
    sub(r'(<div class="nums">).*?(</div>\s*<h2>)',
        lambda mm: mm.group(1) + ''.join(f'<div><b>{a}</b><i>{b}</i></div>' for a, b in nums) + mm.group(2), re.S)
    sub(r'(<div class="sub">Est\. 2002 · )\d+ tours · \d+ countries', rf'\g<1>{len(T)} tours · {countries} countries')
    return s
