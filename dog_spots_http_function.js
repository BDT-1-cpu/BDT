// ============================================================================
//  Big Dogs Tour – "Dog Spots" photo list as a web address (BACKEND)
//  Wix file path:  backend/http-functions.js
//  (If that file already exists, paste everything below the imports into it and
//   merge the import lines at the top.)
//
//  Gives the Dog Spots page the same photo list as backend/dogSpots.web.js, at
//      https://www.bigdogstour.com/_functions/dogSpots
//  so the page can load it itself when the app opens it directly (without the
//  Wix page around it). Nothing else changes: the Wix page still works as before.
// ============================================================================

import { ok, serverError } from 'wix-http-functions';
import { getGallery } from 'backend/dogSpots.web';

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
