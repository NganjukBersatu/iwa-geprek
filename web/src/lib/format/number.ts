/** Reads a number pasted from a spreadsheet: "1.250,50" and "1,250.50" both become 1250.5; "Rp" and spaces are ignored. Null when empty or unreadable. */
export function parseNumber(text: string): number | null {
	let value = text.replace(/rp/gi, '').replace(/\s+/g, '').trim();
	if (value === '') return null;
	const comma = value.lastIndexOf(',');
	const dot = value.lastIndexOf('.');
	if (comma > -1 && dot > -1) {
		value = comma > dot ? value.replace(/\./g, '').replace(',', '.') : value.replace(/,/g, '');
	} else if (comma > -1) {
		value = /,\d{1,3}$/.test(value) && value.indexOf(',') === comma ? value.replace(',', '.') : value.replace(/,/g, '');
	} else if (dot > -1 && /^\d{1,3}(\.\d{3})+$/.test(value)) {
		value = value.replace(/\./g, '');
	}
	const parsed = Number(value);
	return Number.isFinite(parsed) ? parsed : null;
}

/** A stored figure put back into an input the way people type it here: decimal comma, no thousand dots, so parseNumber reads it back unchanged. */
export function numberInput(value: string | number): string {
	return String(Number(value)).replace('.', ',');
}
