import { redirect } from '@sveltejs/kit';

// This route was the original story picker; superseded by /catalog which
// shows every piece of content (panel stories + scenario stories + practice
// scenarios + dialogue scripts + legacy narrative scenes). Zero in-app code
// still links here (grep across frontend/src confirms); only direct URL
// hits or stale bookmarks arrive here, so a 302 lands them on the current
// catalog instead of a half-functional picker.
export const load = () => {
    throw redirect(302, '/catalog');
};
