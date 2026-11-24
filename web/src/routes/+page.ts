import { redirect } from '@sveltejs/kit';
import { PAGES } from '$lib/nav/pages';

export function load() {
	redirect(307, PAGES.dashboard.path);
}
