import { page } from '$app/state';

/** The edit form of a record has its own address: the record's address followed by /edit. */
export const EDIT_SEGMENT = '/edit';

/** Reads the current address, so a record page knows whether to show the record or its edit form. */
export function editAddress() {
	return {
		get editing(): boolean {
			return page.url.pathname.endsWith(EDIT_SEGMENT);
		},
		get recordPath(): string {
			const path = page.url.pathname;
			return path.endsWith(EDIT_SEGMENT) ? path.slice(0, -EDIT_SEGMENT.length) : path;
		},
		get editPath(): string {
			return `${this.recordPath}${EDIT_SEGMENT}`;
		}
	};
}
