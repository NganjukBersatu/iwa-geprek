import { fromDate, parseDateTime } from '@internationalized/date';
import { WIB_ZONE } from './zone';

const INPUT_LENGTH = 'YYYY-MM-DDTHH:MM'.length;

/** An instant as the text a datetime-local input shows, in WIB whatever the zone of the device. */
export function toWibInput(iso: string | null): string {
	if (!iso) return '';
	return fromDate(new Date(iso), WIB_ZONE).toString().slice(0, INPUT_LENGTH);
}

/** The text of a datetime-local input read as WIB and turned back into an instant; empty is null. */
export function fromWibInput(text: string): string | null {
	const value = text.trim();
	return value ? parseDateTime(value).toDate(WIB_ZONE).toISOString() : null;
}
