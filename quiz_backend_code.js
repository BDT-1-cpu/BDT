// ============================================================================
//  Big Dogs Tour – "Quiz League" (BACKEND)
//  Wix file path:  backend/quiz.js
//
//  Keeps the quiz questions and everyone's answers in two Wix collections:
//    QuizQuestions – one row per quiz day (question, options, right answer, date)
//    QuizAnswers   – one row per player per quiz (written by the page, not by hand)
//  Both collections are set to "Admin only", so the only way in or out is this
//  code. The right answer (and the note that goes with it) never leaves Wix
//  until 9pm UK time on the quiz day.
//
//  Called from backend/http-functions.js:
//    GET  https://www.bigdogstour.com/_functions/quiz        -> quizzes, who has answered, league
//    POST https://www.bigdogstour.com/_functions/quizAnswer  -> save one player's pick
// ============================================================================

import wixData from 'wix-data';

// ---- Settings you can change ------------------------------------------------

// Everyone in the WhatsApp group (Display names from the Players sheet, no MDE tag).
export const PLAYERS = [
    'Adam G', 'Adam T', 'Ash', 'Bean', 'Boggy', 'Boysie', 'BT', 'Buysai', 'Buzz', 'Charlie',
    'Coxy', 'DT', 'Fred', 'Gav', 'Glenn', 'Harbo', 'Hulmey', 'Hursty', 'Kenners', 'Kezza',
    'Knoxy', 'Langers', 'Langrish', 'Little', 'Lordy', 'Marshy', 'Oli G', 'Paddy', 'Purlo', 'Ravo',
    'Rick', 'Rob', 'Robbo', 'Rufus', 'Steve', 'Tom', 'Tully', 'Tyzzer',
];

// When a quiz opens and when its answer is revealed, UK time, if the row leaves them blank.
const DEFAULT_OPENS = '00:00';
const DEFAULT_REVEAL = '21:00';

// -----------------------------------------------------------------------------

const QUESTIONS = 'QuizQuestions';
const ANSWERS = 'QuizAnswers';
const AS_ADMIN = { suppressAuth: true };
const LETTERS = 'ABCDEF';

// ---- UK time ------------------------------------------------------------------
// Turns a UK date and clock time ("2027-03-10", "21:00") into a moment in time.
// British Summer Time runs from 01:00 GMT on the last Sunday of March to 01:00 GMT
// on the last Sunday of October.
function lastSunday(year, monthIndex) {
    const last = new Date(Date.UTC(year, monthIndex + 1, 0));
    return last.getUTCDate() - last.getUTCDay();
}

export function ukTime(dateText, timeText) {
    const d = String(dateText || '').trim().match(/^(\d{4})-(\d{1,2})-(\d{1,2})$/);
    const t = String(timeText || '').trim().match(/^(\d{1,2})[:.](\d{2})$/);
    if (!d || !t) return NaN;
    const [y, mo, da] = [+d[1], +d[2], +d[3]];
    const asGmt = Date.UTC(y, mo - 1, da, +t[1], +t[2]);
    const bstStart = Date.UTC(y, 2, lastSunday(y, 2), 1);
    const bstEnd = Date.UTC(y, 9, lastSunday(y, 9), 1);
    const asBst = asGmt - 3600 * 1000;
    return (asBst >= bstStart && asBst < bstEnd) ? asBst : asGmt;
}

// Wix "Date" fields come back as a Date at midnight; text fields as "2027-03-10".
function dateText(v) {
    if (v instanceof Date && !isNaN(v)) {
        const p = n => String(n).padStart(2, '0');
        return `${v.getFullYear()}-${p(v.getMonth() + 1)}-${p(v.getDate())}`;
    }
    const s = String(v || '').trim();
    const uk = s.match(/^(\d{1,2})\/(\d{1,2})\/(\d{4})$/);          // 10/03/2027
    if (uk) return `${uk[3]}-${uk[2].padStart(2, '0')}-${uk[1].padStart(2, '0')}`;
    return s.slice(0, 10);
}

// ---- Reading the collections ---------------------------------------------------

async function fetchAll(collection) {
    let res = await wixData.query(collection).limit(1000).find(AS_ADMIN);
    const items = res.items.slice();
    while (res.hasNext()) {
        res = await res.next();
        items.push(...res.items);
    }
    return items;
}

// One QuizQuestions row -> a tidy quiz (or null if the row is not filled in properly).
function toQuiz(row) {
    const id = String(row.title || '').trim();
    const options = String(row.options || '').split('|').map(s => s.trim()).filter(Boolean);
    const correctText = String(row.correct || '').trim().toUpperCase();
    const correct = /^\d+$/.test(correctText) ? +correctText - 1 : LETTERS.indexOf(correctText);
    const date = dateText(row.quizDate);
    const opensAt = ukTime(date, row.opens || DEFAULT_OPENS);
    const revealAt = ukTime(date, row.reveal || DEFAULT_REVEAL);
    const problems = [];
    if (!id) problems.push('no Quiz ID');
    if (!row.question) problems.push('no question');
    if (options.length < 2) problems.push('fewer than 2 options');
    if (!(correct >= 0 && correct < options.length)) problems.push('right answer is not one of the options');
    if (isNaN(opensAt) || isNaN(revealAt)) problems.push('date or time not understood');
    if (problems.length) {
        console.warn(`Quiz row "${id}" skipped: ${problems.join(', ')}`);
        return null;
    }
    return {
        id,
        day: row.day === undefined || row.day === null || row.day === '' ? '' : String(row.day),
        tag: String(row.tag || '').trim(),
        question: String(row.question).trim(),
        options,
        correct,
        note: String(row.note || '').trim(),
        opensAt,
        revealAt,
    };
}

async function loadQuizzes() {
    const rows = await fetchAll(QUESTIONS);
    return rows.map(toQuiz).filter(Boolean).sort((a, b) => a.opensAt - b.opensAt || a.id.localeCompare(b.id));
}

// ---- What the page sees -------------------------------------------------------

export async function getQuizState() {
    const now = Date.now();
    const [quizzes, answers] = await Promise.all([loadQuizzes(), fetchAll(ANSWERS)]);

    // quizId -> { player -> pick }
    const byQuiz = {};
    for (const a of answers) {
        if (!PLAYERS.includes(a.title)) continue;
        (byQuiz[a.quizId] = byQuiz[a.quizId] || {})[a.title] = a.pick;
    }

    const open = quizzes.filter(q => q.opensAt <= now);
    const next = quizzes.find(q => q.opensAt > now);

    const league = {};
    PLAYERS.forEach(p => { league[p] = { player: p, points: 0, played: 0 }; });

    const out = open.map(q => {
        const picks = byQuiz[q.id] || {};
        const revealed = now >= q.revealAt;
        const base = {
            id: q.id, day: q.day, tag: q.tag, question: q.question, options: q.options,
            opensAt: q.opensAt, revealAt: q.revealAt, revealed,
        };
        if (!revealed) {
            // Before 9pm: names only, never the picks, never the right answer.
            return { ...base, answered: Object.keys(picks).sort() };
        }
        for (const [p, pick] of Object.entries(picks)) {
            league[p].played++;
            if (pick === q.correct) league[p].points++;
        }
        return { ...base, answered: Object.keys(picks).sort(), picks, correct: q.correct, note: q.note };
    });

    const table = Object.values(league)
        .filter(r => r.played > 0)
        .sort((a, b) => b.points - a.points || a.played - b.played || a.player.localeCompare(b.player));

    return {
        type: 'quiz-data',
        now,
        players: PLAYERS,
        quizzes: out,
        nextOpensAt: next ? next.opensAt : null,
        league: table,
    };
}

// ---- Saving a pick -----------------------------------------------------------------
// Returns { ok: true, ... } or { ok: false, status, message }.

export async function saveAnswer(body) {
    const player = String((body && body.player) || '').trim();
    const quizId = String((body && body.quizId) || '').trim();
    const pick = Number(body && body.pick);

    if (!PLAYERS.includes(player)) return { ok: false, status: 400, message: 'Pick your name from the list first.' };

    const quizzes = await loadQuizzes();
    const q = quizzes.find(z => z.id === quizId);
    const now = Date.now();
    if (!q || now < q.opensAt) return { ok: false, status: 404, message: 'That quiz is not open.' };
    if (now >= q.revealAt) return { ok: false, status: 403, message: 'Too late – this one closed at 9pm.' };
    if (!Number.isInteger(pick) || pick < 0 || pick >= q.options.length) {
        return { ok: false, status: 400, message: 'That answer is not one of the options.' };
    }

    // One row per player per quiz: saving again replaces the earlier pick.
    const _id = `${quizId}__${player}`.replace(/[^A-Za-z0-9_-]+/g, '-');
    await wixData.save(ANSWERS, { _id, title: player, quizId, pick, answeredAt: new Date(now) }, AS_ADMIN);
    return { ok: true, player, quizId, pick };
}
