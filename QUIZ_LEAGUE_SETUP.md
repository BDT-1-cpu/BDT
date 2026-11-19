# Quiz League: setting it up on Wix

The quiz page lives on GitHub Pages (`Quiz League.html`) and is shown on a bigdogstour.com page through one Embed HTML box, like the other pages. Answers are kept in two Wix collections. The page talks to Wix through two web addresses:

- `https://www.bigdogstour.com/_functions/quiz` lists the open quizzes, who has answered and the league.
- `https://www.bigdogstour.com/_functions/quizAnswer` saves a pick.

The right answer stays inside Wix until 9pm UK time on the quiz day. Before then nobody can see it, not even by opening the web address.

No page code is needed on the Wix page this time.

## Files

| File in this folder | Where it goes in Wix |
| --- | --- |
| `quiz_backend_code.js` | new file `backend/quiz.js` |
| `quiz_http_functions_full.js` | replaces all of `backend/http-functions.js` (keeps Dog Spots as it was) |
| `quiz_trial_questions.csv` | imported into the `QuizQuestions` collection |
| `Quiz League.html` | GitHub Pages (pushed with the rest of the repo) |

## Step 1: the QuizQuestions collection

1. In the Wix editor open **CMS** → **Create Collection** → name it exactly `QuizQuestions`.
2. Set its permissions to private: **More actions** (⋯) → **Permissions & privacy** → **Private** (only admins can read or write). This keeps the right answers hidden.
3. Rename the built-in **Title** field to `Quiz ID` (its Field ID stays `title`, which is what the code uses).
4. Add these fields. When you add each one, check the **Field ID** shown under the name matches the second column exactly.

| Field name | Field ID | Type |
| --- | --- | --- |
| Day | `day` | Text |
| Quiz Date | `quizDate` | Text |
| Tag | `tag` | Text |
| Question | `question` | Text |
| Options | `options` | Text |
| Correct | `correct` | Text |
| Note | `note` | Text |
| Opens | `opens` | Text |
| Reveal | `reveal` | Text |

5. Import the trial quizzes: **More actions** → **Import from CSV** → choose `quiz_trial_questions.csv` → match each CSV column to the field of the same name (Quiz ID → Quiz ID/title) → **Import**.

How a row is filled in:

- **Quiz ID**: any unique code. Trial rows are `TRIAL-49` etc.; use `D49`, `D48` … for the real countdown so they never mix with the trial.
- **Day**: the countdown number. The page shows it as "Day 49".
- **Quiz Date**: the day the quiz runs, as `2027-03-10` (or `10/03/2027`).
- **Options**: the answers separated by `|`, for example `Boggy | Hursty | Buzz | Knoxy`. Two to six options.
- **Correct**: the letter of the right answer (`A`, `B`, `C` …) or its number (`1`, `2` …).
- **Note**: the line shown with the answer at 9pm (optional).
- **Opens** and **Reveal**: UK times, normally left blank. Blank means the quiz opens at midnight and the answer is revealed at 9pm (`21:00`) that day. British Summer Time is handled for you.

A row that is not filled in properly (no question, the right answer not one of the options, a date the code cannot read) is skipped and does not appear on the page.

## Step 2: the QuizAnswers collection

1. **CMS** → **Create Collection** → name it exactly `QuizAnswers`.
2. Permissions: **Private**, as above.
3. Rename **Title** to `Player` (Field ID stays `title`).
4. Add these fields:

| Field name | Field ID | Type |
| --- | --- | --- |
| Quiz ID | `quizId` | Text |
| Pick | `pick` | Number |
| Answered At | `answeredAt` | Date and Time |

Leave it empty. The page fills it: one row per player per quiz. Pick is 0 for A, 1 for B, and so on.

## Step 3: the backend code

1. Turn on **Dev Mode** if it is not on. In the left panel open **Backend** (the `{ }` code files).
2. Add a new file in Backend called `quiz.js`. Paste in all of `quiz_backend_code.js`.
3. Open `http-functions.js`. Before you replace it, check it only holds the Dog Spots code (`get_dogSpots`). If it has anything else in it, stop and tell Claude. Otherwise select everything, delete it, and paste in all of `quiz_http_functions_full.js`.
4. **Publish** the site. The web addresses only work on the published site.
5. Check: open `https://www.bigdogstour.com/_functions/quiz` in a browser. You should see text starting `{"type":"quiz-data"`. Before the first trial date `quizzes` is an empty list `[]` and `nextOpensAt` is a number; that is right.
6. Also open `https://www.bigdogstour.com/_functions/dogSpots` to check Dog Spots still works.

## Step 4: the Wix page

1. Add a new page called **Quiz** (Pages → + Add Page → Blank). Its address will be `https://www.bigdogstour.com/quiz` (check under Page settings → SEO basics → URL slug, and set it to `quiz`).
2. Set it up like the other pages (see `WIX_EMBED_LINKS.md`): page background `#050B09`, one **Embed HTML** box, 1300 wide on desktop.
3. Click the box → **Enter Code** → **Website address** → paste `https://bdt-1-cpu.github.io/BDT/Quiz%20League.html` → **Update**.
4. On the **mobile** editor make the box full width and tall (about 1400), as this page will mostly be used on phones.
5. **Publish**.

## Step 5: trial

The trial quizzes open on 21, 22 and 23 November 2026 (change the Quiz Date in the CMS to move them). On each trial day:

1. Open `https://www.bigdogstour.com/quiz` on your phone, pick your name, answer.
2. Ask one or two others to try it, or open it on a second device and answer as someone else.
3. After 9pm check the right answer, the picks and the league show.

To try a reveal without waiting until 9pm, set that row's **Reveal** to a time a few minutes ahead (for example `14:35`), wait, and refresh the page.

After the trial, delete the three `TRIAL-` rows from `QuizQuestions` and all rows from `QuizAnswers`, so the league starts at zero.

## Adding the real quiz days

Add a row to `QuizQuestions` for each quiz day (or import a CSV in the same layout as `quiz_trial_questions.csv`). Nothing else needs changing: the quiz appears on the page from midnight on its date. The link in each WhatsApp caption is `https://www.bigdogstour.com/quiz` (never the GitHub address, which shows "use bigdogstour.com" when opened on its own).

The player list is in `backend/quiz.js` (`PLAYERS`, near the top). Change it there if someone joins or leaves the WhatsApp group, then Publish.
