import sys, json

# Per-team retint of the "clubhouse-at-night" palette: same gold trim and
# lettering, but the deep felt/background hue swaps to red for the Bloodhounds
# embed and blue for the Retrievers embed instead of the universal green.
TEAM_THEMES = {
    # Sampled directly from the diagonal-stripe background of the player-profile
    # graphics themselves (pixel-picked from the actual portrait/landscape
    # images), so the page felt reads as the same red/blue as the profile
    # cards rather than a separately-invented approximation.
    'bh': """
  :root{
    /* "deep true red" - chosen from a set of swatches (a pure, fully-saturated
       red hue rather than a pull from any one image sample), at the same
       brightness/darkness relationships as the rest of the felt palette. */
    --bg0:#100101;
    --bg-grad-a:#250202;
    --bg-grad-b:#090101;
    --felt:#540000;
    --felt-hi:#800000;
    --felt-glass: rgba(128,0,0,0.55);
    --bg-glow-a: rgba(255,0,0,0.18);
    --bg-glow-b: rgba(240,197,102,0.05);
  }
""",
    'rt': """
  :root{
    /* "electric / indigo blue" - chosen from a set of swatches, at the same
       brightness/darkness relationships as the rest of the felt palette. */
    --bg0:#030511;
    --bg-grad-a:#060B29;
    --bg-grad-b:#02030A;
    --felt:#091357;
    --felt-hi:#15258C;
    --felt-glass: rgba(21,37,140,0.55);
    --bg-glow-a: rgba(0,34,255,0.17);
    --bg-glow-b: rgba(240,197,102,0.05);
  }
""",
}

def combine(page_path, webdata_path, appjs_path, out_path, team=None):
    page = open(page_path, encoding='utf-8').read()
    webdata = open(webdata_path, encoding='utf-8').read()
    # validate it's proper JSON (compact, no need to re-serialize)
    json.loads(webdata)
    appjs = open(appjs_path, encoding='utf-8').read()
    theme_css = TEAM_THEMES.get(team, '')
    team_name = {'bh': 'Bloodhounds', 'rt': 'Retrievers'}.get(team, '')
    out = (page.replace('/*__TEAM_THEME__*/', theme_css)
               .replace('__WEBDATA__', webdata)
               .replace('__APPJS__', appjs)
               .replace('__TEAM_NAME__', team_name))
    open(out_path, 'w', encoding='utf-8').write(out)
    print(f"wrote {out_path}: {len(out)} bytes (team={team!r})")

if __name__ == '__main__':
    args = sys.argv[1:6]
    page_path, webdata_path, appjs_path, out_path = args[:4]
    team = args[4] if len(args) > 4 else None
    combine(page_path, webdata_path, appjs_path, out_path, team)
