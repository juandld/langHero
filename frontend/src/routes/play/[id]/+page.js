import { redirect } from '@sveltejs/kit';

// Legacy run-id player (loaded via GameView + runStore from the pre-pivot
// scenarios system). Zero in-app code links here — every current call site
// targets /play/story/{storyId} instead. 302 to /catalog so a direct URL
// visit lands on today's canonical content index rather than an orphaned
// legacy surface. ssr/csr defaults are fine — load() throws before render.
export const load = () => {
    throw redirect(302, '/catalog');
};

