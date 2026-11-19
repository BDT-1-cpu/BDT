// ============================================================================
//  Big Dogs Tour – web addresses served by Wix (BACKEND)
//  Wix file path:  backend/http-functions.js
//
//  This is the WHOLE file: the Dog Spots list (unchanged) plus the Quiz League.
//  Select everything in backend/http-functions.js, delete it, paste this in.
//
//    https://www.bigdogstour.com/_functions/dogSpots     Dog Spots photo list
//    https://www.bigdogstour.com/_functions/quiz         Quiz League: quizzes, who has answered, league
//    https://www.bigdogstour.com/_functions/quizAnswer   Quiz League: save a pick (POST)
// ============================================================================

import { ok, badRequest, forbidden, notFound, serverError, response } from 'wix-http-functions';
import { getGallery } from 'backend/dogSpots.web';
import { getQuizState, saveAnswer } from 'backend/quiz';

// ---- Dog Spots ----------------------------------------------------------------

// Keep the list for an hour between requests (as dogSpots.web.js does), so the
// Media Manager is not searched on every visit.
const KEEP_MS = 60 * 60 * 1000;
let saved = null;
let savedAt = 0;

const HEADERS = {
    'Content-Type': 'application/json',
    'Access-Control-Allow-Origin': '*',
    'Cache-Control': 'public, max-age=300',
};

export async function get_dogSpots(request) {
    try {
        if (!saved || Date.now() - savedAt > KEEP_MS) {
            saved = await getGallery();
            savedAt = Date.now();
        }
        return ok({ headers: HEADERS, body: JSON.stringify({ type: 'dogspots-data', categories: saved }) });
    } catch (err) {
        console.error('Dog Spots list:', err);
        return serverError({ headers: HEADERS, body: JSON.stringify({ type: 'dogspots-data', categories: [], error: true }) });
    }
}

// ---- Quiz League --------------------------------------------------------------

// Never cached: the page must see new answers and the 9pm reveal straight away.
const QUIZ_HEADERS = {
    'Content-Type': 'application/json',
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type',
    'Cache-Control': 'no-store',
};

export async function get_quiz(request) {
    try {
        return ok({ headers: QUIZ_HEADERS, body: JSON.stringify(await getQuizState()) });
    } catch (err) {
        console.error('Quiz state:', err);
        return serverError({ headers: QUIZ_HEADERS, body: JSON.stringify({ type: 'quiz-data', error: true }) });
    }
}

export async function post_quizAnswer(request) {
    try {
        let body = null;
        try { body = JSON.parse(await request.body.text()); } catch (e) { body = null; }
        const result = await saveAnswer(body);
        if (result.ok) return ok({ headers: QUIZ_HEADERS, body: JSON.stringify(result) });
        const send = result.status === 403 ? forbidden : result.status === 404 ? notFound : badRequest;
        return send({ headers: QUIZ_HEADERS, body: JSON.stringify(result) });
    } catch (err) {
        console.error('Quiz answer:', err);
        return serverError({ headers: QUIZ_HEADERS, body: JSON.stringify({ ok: false, message: 'Could not save. Try again.' }) });
    }
}

// Browsers may check first whether they are allowed to send a POST.
export function options_quizAnswer(request) {
    return response({ status: 204, headers: QUIZ_HEADERS });
}
