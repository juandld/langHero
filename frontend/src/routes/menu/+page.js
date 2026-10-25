import { redirect } from '@sveltejs/kit';

// Legacy "Saved Runs" manager tied to the pre-pivot runsStore system. Its
// "Play" button navigated to /play/[id] (now a 302 to /catalog) and its data
// came from a run model that no longer integrates with the current save flow
// (LANGHERO_STORY_PROGRESS_V1 localStorage, surfaced on /profile). Zero
// in-app code links to /menu — only reachable by direct URL / stale bookmark.
// 302 to /profile, which is today's canonical my-progress surface.
// ssr/csr defaults left in place — load() throws before any render anyway.
export const load = () => {
    throw redirect(302, '/profile');
};

