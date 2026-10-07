// ============================================================================
//  Big Dogs Tour – "Dog Spots" page code
//  The page holds one Embed HTML element (ID: dogSpotsHtml) containing
//  bdt_dog_spots.html. This code fetches the photos from the Media Manager
//  (backend/dogSpots.web.js) and passes them into that embed.
// ============================================================================

import { getGallery } from 'backend/dogSpots.web';
import wixLocationFrontend from 'wix-location-frontend';

let payload = null;
let loading = null;

function load() {
    if (!loading) {
        loading = getGallery()
            .then(categories => { payload = { type: 'dogspots-data', categories, start: wixLocationFrontend.query.category || '' }; })
            .catch(err => { console.error('Dog Spots:', err); payload = { type: 'dogspots-data', categories: [], error: true }; });
    }
    return loading;
}

function send() {
    if (payload) $w('#dogSpotsHtml').postMessage(payload);
}

$w.onReady(function () {
    load().then(send);
    // The embed asks for the data once it has loaded (it may load after the data arrives).
    $w('#dogSpotsHtml').onMessage(event => {
        if (event.data && event.data.type === 'dogspots-ready') load().then(send);
    });
});
