import { redirect } from '@sveltejs/kit';

// Path-param variant of the story route. Zero in-app callers — the live code
// (frontend/src/routes/+page.svelte storyUrl()) uses /story?id=X&lang=Y
// (query-param form on the sibling route) for every scenario-type story.
// This folder's +page.svelte exists but is unreachable through the UI. 302
// to /catalog so direct URL hits land on today's content index.
export const load = () => {
    throw redirect(302, '/catalog');
};
