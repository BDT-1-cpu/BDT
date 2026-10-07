// ============================================================================
//  Big Dogs Tour – "Dog Spots" gallery (BACKEND)
//  Wix file path:  backend/dogSpots.web.js   (FASTER VERSION – results cached for an hour)
//
//  Reads the "Dog Spots" folder in the Wix Media Manager and returns its
//  sub-folders (categories) and the photos inside each one, plus any extra
//  category folders listed below (e.g. Laughs > Celebridogs).
//  Because it reads the Media Manager live, any photo you upload to one of
//  those folders appears on the site automatically – nothing to re-publish.
// ============================================================================

import { Permissions, webMethod } from 'wix-web-module';
import { mediaManager } from 'wix-media-backend';

// ---- Settings you can change ------------------------------------------------

// Name of the head folder in the Wix Media Manager (must match exactly).
const ROOT_FOLDER_NAME = 'Dog Spots';

// Sub-folders that should NOT appear as gallery categories (not case-sensitive).
const EXCLUDED_FOLDERS = ['to do', 'new folder', 'resized', 'video'];

// Extra folders that live OUTSIDE the "Dog Spots" folder but should still appear as
// categories on the page. Each is found by name anywhere in the Media Manager
// (preferring one inside a "Laughs" folder if there is more than one).
const EXTRA_CATEGORY_FOLDERS = ['Celebridogs'];

// -----------------------------------------------------------------------------

const PAGE_SIZE = 100;

// Alphabetical, ignoring case, with "2" sorting before "10".
const collator = new Intl.Collator('en-GB', { sensitivity: 'base', numeric: true });

async function listAllFolders(parentFolderId) {
    const all = [];
    let skip = 0;
    // Keep paging until the Media Manager returns an empty page.
    for (;;) {
        const filters = parentFolderId ? { parentFolderId } : {};
        const page = await mediaManager.listFolders(filters, undefined, { limit: PAGE_SIZE, skip });
        if (!page || page.length === 0) break;
        all.push(...page);
        skip += page.length;
    }
    return all;
}

async function listAllFiles(parentFolderId) {
    const all = [];
    let skip = 0;
    for (;;) {
        const page = await mediaManager.listFiles({ parentFolderId }, undefined, { limit: PAGE_SIZE, skip });
        if (!page || page.length === 0) break;
        all.push(...page);
        skip += page.length;
    }
    return all;
}

// Finds a folder by name anywhere in the Media Manager (searches up to 4 levels deep),
// so it can sit at the top level or inside other folders such as "Site Files" or "Laughs".
// If several folders share the name, one inside a folder called preferredParent wins.
async function findFolder(name, preferredParent = 'laughs') {
    const target = name.trim().toLowerCase();
    let level = (await listAllFolders()).map(f => ({ f, parent: '' }));
    const matches = [];
    for (let depth = 0; depth < 4 && level.length; depth++) {
        level.filter(x => (x.f.folderName || '').trim().toLowerCase() === target).forEach(x => matches.push(x));
        if (matches.length) break;
        const next = await Promise.all(level.map(async x =>
            (await listAllFolders(x.f.folderId)).map(f => ({ f, parent: (x.f.folderName || '').trim().toLowerCase() }))));
        level = next.flat();
    }
    if (!matches.length) return null;
    return (matches.find(x => x.parent === preferredParent) || matches[0]).f;
}

async function findRootFolder() {
    const root = await findFolder(ROOT_FOLDER_NAME);
    if (!root) throw new Error(`Media Manager folder "${ROOT_FOLDER_NAME}" was not found.`);
    return root;
}

// Turns a file name into a tidy caption, e.g.
//   "Big Dog Betting_opt (2).jpg" -> "Big Dog Betting"
//   "Little's Coffee2.jpg"        -> "Little's Coffee"
//   "Monkey 47.jpg"               -> "Monkey 47"   (real numbers are kept)
//   "PHOTO-2026-05-05-06-03-35"   -> ""            (camera names get no caption)
export function toCaption(fileName) {
    let s = String(fileName || '').replace(/\.[a-z0-9]+$/i, '');   // extension
    for (let i = 0; i < 2; i++) {
        s = s.replace(/\s*\(\d+\)\s*$/, '');                        // " (2)"
        s = s.replace(/[\s_-]*(opt|optimi[sz]ed|resized|edited|copy)$/i, ''); // "_opt"
    }
    s = s.replace(/([A-Za-z'’)\s])\s*[23]$/, '$1');                  // duplicate marker "2"/"3"
    s = s.replace(/_/g, ' ').replace(/\s+/g, ' ').trim();
    if (/^(photo|img|image|dsc|pxl|whatsapp image)[\s_-]*\d/i.test(s)) return '';
    return s;
}

// ---- Web method called by the page ------------------------------------------

function mediaId(f) {
    const m = String(f.fileUrl || '').match(/^wix:image:\/\/v1\/([^/#]+)/);
    return m ? m[1] : (f.fileName || '');
}

// Returns every category (sub-folder) with its photos, both in alphabetical order:
//   [{ name: 'Pubs', photos: [{ id: '588d17_...~mv2.jpg', caption: 'Bad Monkey' }, ...] }, ...]
// CACHED: Wix keeps the result for CACHE_SECONDS, so visitors get the gallery instantly instead of
// waiting for the whole Media Manager to be searched on every visit. New uploads appear once the
// cache expires (or straight away after re-publishing the site).
const CACHE_SECONDS = 3600;   // 1 hour

export const getGallery = webMethod(Permissions.Anyone, async () => {
    const root = await findRootFolder();
    const subFolders = (await listAllFolders(root.folderId))
        .filter(f => !EXCLUDED_FOLDERS.includes((f.folderName || '').trim().toLowerCase()));

    // Add the extra category folders (skipping any that are missing or already included).
    for (const name of EXTRA_CATEGORY_FOLDERS) {
        const extra = await findFolder(name);
        if (extra && !subFolders.some(f => f.folderId === extra.folderId ||
                (f.folderName || '').trim().toLowerCase() === name.trim().toLowerCase())) {
            subFolders.push(extra);
        }
    }
    subFolders.sort((a, b) => collator.compare(a.folderName, b.folderName));

    return Promise.all(subFolders.map(async (folder) => {
        const files = await listAllFiles(folder.folderId);
        const photos = files
            .filter(f => f.mediaType === 'image' || String(f.mimeType || '').startsWith('image/'))
            .map(f => {
                const name = f.originalFileName || f.fileName || '';
                return { id: mediaId(f), caption: toCaption(name), sortKey: name.replace(/\.[a-z0-9]+$/i, '') };
            })
            .filter(p => p.id)
            .sort((a, b) => collator.compare(a.sortKey, b.sortKey))
            .map(({ id, caption }) => ({ id, caption }));
        return { name: folder.folderName, photos };
    }));
}, { cache: { tags: ['dogspots'], ttl: CACHE_SECONDS } });
