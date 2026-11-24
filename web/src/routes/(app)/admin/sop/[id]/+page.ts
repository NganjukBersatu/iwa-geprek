import { redirect } from '@sveltejs/kit';
import { sopEditPath } from '$lib/nav/pages';

/** A procedure has no page to read, only its editor, so an old link to it opens the editor. */
export function load({ params }: { params: { id: string } }): never {
	redirect(307, sopEditPath(params.id));
}
