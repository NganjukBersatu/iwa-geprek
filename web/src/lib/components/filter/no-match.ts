import { controlText } from '$lib/text/controls';
import { format } from '$lib/text/format';
/** Empty-list text that names what actually narrowed the list: the search, the filters, or both. */
export function noMatchText(subject: string, searching: boolean, filtering: boolean): string | null {
	if (searching && filtering) return format(controlText.noMatchSearchAndFilter, { subject: subject });
	if (searching) return format(controlText.noMatchSearch, { subject: subject });
	if (filtering) return format(controlText.noMatchFilter, { subject: subject });
	return null;
}
