"""Learns where every table on the Statistics and Trophies pages comes from in the Master Playbook.

    python3 tools/sitedata_learn.py <recalculated playbook.xlsx> Statistics.html Trophies.html

For each table (block) it finds the sheet, the header row, the column for each heading and where the rows
start, by matching the rows already on the page against the Playbook's calculated values. The result is
saved as tools/sitedata_spec.json and used by tools/update_site.py to refresh the pages after a tour.
"""
import json, re, sys, warnings
import openpyxl
warnings.filterwarnings('ignore')


def norm(v):
    if v is None:
        return ''
    if isinstance(v, bool):
        return str(v)
    if isinstance(v, (int, float)):
        f = round(float(v), 4)
        return int(f) if f == int(f) else f
    if hasattr(v, 'isoformat'):
        return v.isoformat()[:10]
    s = str(v).strip()
    if re.fullmatch(r'-?\d+(\.\d+)?', s):
        f = round(float(s), 4)
        return int(f) if f == int(f) else f
    return s


def plain(s):
    import unicodedata
    return ''.join(ch for ch in unicodedata.normalize('NFKD', s) if not unicodedata.combining(ch))


def same(a, b):
    """Playbook value a matches page value b (allowing the page's rounding, % and accent formatting)."""
    a, b = norm(a), norm(b)
    if isinstance(b, str) and re.fullmatch(r'-?\d+(\.\d+)?%', b) and isinstance(a, (int, float)):
        return abs(a * 100 - float(b[:-1])) < 0.6
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        return abs(a - b) < 0.006 or (abs(a - b) < 0.051 and round(a, 1) == b)
    if isinstance(a, str) and isinstance(b, str):
        return a == b or plain(a) == plain(b)
    return False


def webdata(page):
    s = open(page, encoding='utf-8').read()
    return json.loads(re.search(r'<script id="webdata" type="application/json">(.*?)</script>', s, re.S).group(1))


def learn_block(grid, rows):
    """Find (start_row, [col per field]) so that grid matches the given rows. Returns None if not found."""
    if not rows:
        return None
    first = rows[0]
    nf = len(first)
    key = next((j for j, v in enumerate(first) if norm(v) != ''), None)
    if key is None:
        return None
    for r, line in enumerate(grid):
        for c0, v in enumerate(line):
            if not same(v, first[key]):
                continue
            # map every field to a column in this row, left to right where possible
            def cell(i, c):
                return grid[r + i][c] if r + i < len(grid) and c < len(grid[r + i]) else None
            # each field: the column that matches it on (nearly) every row. Text columns are allowed a
            # few differences - those are places where the page has drifted from the Playbook.
            cols = []
            for j in range(nf):
                score = {c: sum(same(cell(i, c), rows[i][j]) for i in range(len(rows))) for c in range(len(line))}
                need = max(1, int(len(rows) * 0.85)) if all(isinstance(norm(x[j]), (int, float)) or norm(x[j]) == '' for x in rows) else max(1, int(len(rows) * 0.6))
                cand = [c for c in score if score[c] >= need and score[c] == max(score.values())]
                if not cand:
                    break
                prev = max(cols, default=-1)
                cols.append(([c for c in cand if c > prev] or cand)[0])
            if len(cols) == nf:
                return r, cols
    return None


def main():
    wb = openpyxl.load_workbook(sys.argv[1], data_only=True)
    grids = {n: [list(r) for r in wb[n].iter_rows(values_only=True)] for n in wb.sheetnames}
    spec, missing = {}, []
    for page in sys.argv[2:]:
        W = webdata(page)
        for key, sh in W['sheets'].items():
            for bi, b in enumerate(sh['blocks']):
                names = ([key] if key in grids else []) + [n for n in wb.sheetnames if n != key]
                hit = None
                for n in names:
                    hit = learn_block(grids[n], b['rows'])
                    if hit:
                        hit = (n,) + hit
                        break
                if hit:
                    n, r0, cols = hit
                    g = grids[n]
                    nxt = g[r0 + len(b['rows'])] if r0 + len(b['rows']) < len(g) else []
                    keycol = cols[0]
                    grows = not nxt or norm(nxt[keycol] if keycol < len(nxt) else None) == ''
                    fmt = []
                    for j in range(len(cols)):
                        vals = [x[j] for x in b['rows'] if norm(x[j]) != '']
                        if vals and all(isinstance(v, str) and v.endswith('%') for v in vals):
                            fmt.append('pct')
                        elif vals and all(isinstance(v, (int, float)) for v in vals) and any(isinstance(v, float) for v in vals):
                            fmt.append('round2')
                        elif vals and all(isinstance(v, str) for v in vals):
                            fmt.append('str')
                        else:
                            fmt.append('')
                    spec.setdefault(page, {}).setdefault(key, {})[str(bi)] = {
                        'sheet': n, 'row': r0, 'cols': cols, 'n': len(b['rows']),
                        'extent': 'until_blank' if grows else 'fixed', 'fmt': fmt}
                else:
                    missing.append((page, key, bi, len(b['rows'])))
    json.dump(spec, open('tools/sitedata_spec.json', 'w'), indent=1)
    found = sum(len(v) for p in spec.values() for v in p.values())
    print('tables located:', found, '| not located:', len(missing))
    for m in missing:
        print('  missing', m)


if __name__ == '__main__':
    main()
