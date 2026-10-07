# BDT year pages (BDT 2002 – BDT 2026)

One tabbed page per tour, in the same dark clubhouse style and standard crest header as the Trophies / Statistics pages.

Tabs: Overview · Venue · Captains · Accommodation · Golf Courses · Itinerary · Teams · Team Announcement · Ryder Cup · Leaderboard · Trophies · Summary · Videos · Photos. A tab with no data hides itself (e.g. no Ryder Cup tab for 2002/2003).

## Files
| File | What it is |
|---|---|
| `BDT <year>.html` | The finished page for that year (Wix shows it from GitHub Pages – nothing to paste) |
| `tour_page_template.html` | Shared design/layout used for every year |
| `build_tour_page.py` | Builds a year's page; `tools/build_site.py` runs it for every year with results |
| `<year>.json` | Per-tour photo IDs and text that aren't in the playbook (`tour_media/<year>.json` when building) |
| `BDT_<year>_RyderCup_<n>.jpg`, `BDT_<year>_Leaderboard_<n>.jpg` | The results boards and leaderboards shown on each page |

## Where the data comes from
- **Master Playbook** – dates, captains, players on tour, team sheets (photo order), every Ryder Cup match, individual Stableford scores and positions, trophies and reasons, shirt/logo IDs.
- **bdt_tour_courses.html** – tee-shot and scorecard photos, round dates, best scores, field averages, head-shots, crest.
- **bdt_trophies.html** – trophy icons and one-line descriptions.
- **tour_media/<year>.json** – hero photo, captain photos, accommodation photos (+ optional name/blurb), itinerary pages, team photos, team announcement videos, original results boards and leaderboards, summary banner/text, video sections (e.g. Photo Slideshow, Videodography), the full photo gallery, map search.

Videos are given as the Vimeo number, e.g. `{"vimeo": "934269157", "title": "BDT 2024 Team Announcement"}` (or `"youtube": "<id>"`). Accommodation and itinerary pages show as a slideshow with thumbnails; the photo gallery shows 60 at a time with Show more / Show all, and the enlarged view steps through every photo.

## Making another year
After a tour, `tools/apply_results.py` (results into the Playbook, and a blank `<year>.json`) and then
`tools/build_site.py` build the new page with every other page – see the main README. Afterwards fill in the
photo IDs in `<year>.json` (the 32-character code after `588d17_` in a Wix image address) and run
`tools/build_site.py` again. Leave anything unknown empty.

Optional extras in the JSON: `summary.text` (blank line between paragraphs), `summary.link`, `accommodation.name`/`blurb`, `venue.blurb`, captions on any photo, and `itinerary_extra` to relabel a day, e.g. `{"2024-05-10": {"title": "Boat trip", "text": "..."}}`.

## House style for page headings (agreed with PD)
Every new page uses the **Option C themed heading**: the standard Big Dogs Tour heading (crest, kicker,
gold title, red/blue stripe) over a background that matches the page's subject – never an unrelated photo.
- Stats pages: `header_themes.py` – statistics (Ryder Cup margins chart), trophies (the trophies),
  courses (tee-shot mosaic), facts (outlined headline numbers), handicaps (scorecard), dogspots (paw prints).
  Numbers come from the playbook each time. Add a new theme function for a new page subject.
- Tours landing page: mosaic of every tour's statement photo. Tour-year pages: that tour's own photo.
- Team pages: the team photo.

