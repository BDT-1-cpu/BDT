# Big Dogs Tour website – how it works (October 2026)

This repository is the **master copy of every page on www.bigdogstour.com**. Read this before changing anything.

## How the site is put together
- The site itself is Wix (menus, page names, addresses, header/footer, the Contact form, the Blog).
- Each Wix page holds one **Embed HTML box set to "Website address"**. It shows a page from this repository,
  served by GitHub Pages at `https://bdt-1-cpu.github.io/BDT/<file>`. The list of which file each Wix page shows
  is in `WIX_EMBED_LINKS.md`.
- So **changing a file here and pushing it to the `main` branch updates the live site within about 10 minutes.**
  If a change hasn't appeared after 15 minutes, check the repository's Actions tab: each push should start a
  "pages build and deployment" run. If none started (in Oct 2026 pushes from a Claude session sometimes did not
  start one), make any small edit to a file on the GitHub website (Claude updates `last-publish.txt` that way), which always
  starts one and publishes everything.
  Nothing needs pasting into Wix and Wix doesn't need publishing.
- The repository is **public**. Never put the Master Playbook or anything with personal details (dates of birth etc.) here.
  The pages carry a "noindex" tag (search engines don't list them) and show only a "go to www.bigdogstour.com" note
  when opened on their own rather than inside the site or the app. `tools/page_guard.py` adds both – run it after
  adding a new page. Dates of birth stay in the Playbook only: the site shows ages, worked out by the builder.

## Where things live
| What | Where | Notes |
| --- | --- | --- |
| Website pages | this repository (`*.html`) | The only copy to edit. Older copies in `F:\Big Dogs Tour\Stats\Claude Workings` are out of date. |
| Master Playbook | Paul's desktop | Private. Send it to Claude when it needs updating. |
| iPhone app | `BDT-1-cpu/bigdogstour-app` repository | A wrapper that shows the website. Only needs a new build when the app itself changes. |
| Dog Spots photos | Wix Media Manager | The list is cached in `dogspots.json`; refresh with `node tools/refresh_dogspots.js` after adding photos. |
| Dog Spots page code | Wix (Dev Mode) | Copies are in `dog_spots_page_code.js` (page) and `dog_spots_backend_code.js` (backend `dogSpots.web.js`). |

## Page files
| Wix page | File |
| --- | --- |
| Home | `Home.html` |
| Tours / BDT 2002–2027 | `Tours.html`, `BDT 2002.html` … `BDT 2027.html` |
| Statistics, Trophies, Courses, Handicaps | `Statistics.html`, `Trophies.html`, `Courses.html`, `Handicaps.html` |
| Trivia (`/trivia`) | `Facts & Figures.html` (file name kept so the Wix link doesn't change) |
| Bloodhounds, Retrievers | `Bloodhounds.html`, `Retrievers.html` |
| History | `History.html` – if the Moments timeline is regenerated with `build_history.py`, run `tools/build_history.py` afterwards to add the four other layouts back |
| Dog Spots, Nicknames, Videos (`/videos`), Rules | `Dog Spots.html`, `Nicknames.html`, `Tour Videos.html`, `Rules, Privacy & Support.html` |

## Tour results (from 2027)
1. Before the tour, update the `TOUR` settings at the top of `scorer.html`: place, country, dates, accommodation and,
   for each round, the course (short name as used in the Playbook), its full name, the day it is played and the format.
2. On tour, the scorer uses **https://bdt-1-cpu.github.io/BDT/scorer.html** on their phone (no login; answers are kept
   on that phone): teams, captains, **handicaps**, shirts, first-timers, every match, every Stableford score,
   final positions and trophies (with reasons). They press **Send to Paul**; Paul checks the message.
3. Paul gives Claude the message and the Playbook. Claude runs
   `python3 tools/apply_results.py results.txt "Big Dogs Tour - Master Playbook.xlsx"`. It adds the rows to the input
   sheets (Tours, Players, Team Sheets, Tour Shirts, RC Matches, Individual, Trophies, Handicaps – handicaps only change for players due
   to tour, including anyone who pulled out, whom the scorer adds; everyone else keeps last year's) without touching anything else, and saves the country, round days and full course names
   in `<year>.json` here. Then the Playbook's **Checks** tab should say ALL OK.
4. Claude runs `python3 tools/build_site.py "Big Dogs Tour - Master Playbook.xlsx"`, which rebuilds every page that
   shows Playbook figures (Statistics, Trophies, Courses, Handicaps, Bloodhounds, Retrievers, Trivia, Home, Tours and
   every tour-year page, including the new one) and prints what changed. Paul checks, then Claude pushes to `main`.
5. By hand afterwards (not in the scorer's message): the tour notes on the Playbook's Tours sheet, the photos and videos for the new tour page (`<year>.json`), tee-shot and scorecard photos
   on the Courses page, the next tour on the Home page and in `scorer.html`.

Rehearsed in October 2026 by taking 2026 out of a copy of the Playbook and the site, re-entering it through the scorer
page and rebuilding: every result, stat and page came back identical apart from the hand-added items in step 5.
The Playbook's Placings sheet has year columns up to 2027 – before the 2028 tour, ask Claude to add more.

## Decisions agreed with Paul (keep to these)
- Trophy names: **Cheat** (not "Ashley Hurst Award") and **Seve & Olly**.
- Captains tab (Trivia): each year and photo border in the colour of the team that won or retained the cup.
- 2002–2005 have finishing positions but no Stableford scores (BT, Boysie and Little were MC in 2004); the 36s once shown as
  those years' best rounds were placeholders, so those scores show as not recorded.
- Charlie Parish's 2005 handicap is 26. Robbo's 9 and Paddy's 48 (both 2003 Round I, La Manga North) are the only 2003 scores.
- On desktop, switching tabs or tiles changes the content without scrolling the page.
- Every page uses the dark clubhouse style; non-selected tabs and sub-tabs have off-white text.
- Mobile: Wix embed boxes are 560px high (section 580px); desktop boxes about 760px.

## Working on the site with Claude
- **Claude Code (cloud):** start a session with this repository (and `bigdogstour-app` for the app). Ask for the change;
  Claude edits, tests, and pushes to `main`.
- **Claude Cowork (desktop):** clone this repository to the PC (e.g. with GitHub Desktop) and tell Cowork to work only in
  that folder. After a change, publish it with GitHub Desktop (**Commit** then **Push**). Don't edit the old copies in
  `Claude Workings`, and don't paste code into Wix any more.
- Always fetch/pull the latest from GitHub before starting, so the two ways of working don't overwrite each other.
