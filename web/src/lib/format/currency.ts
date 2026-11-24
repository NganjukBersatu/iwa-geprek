type Amount = number | string | null | undefined;

export function formatRupiah(value: Amount): string {
	const amount = Number(value);
	if (!Number.isFinite(amount)) return 'Rp 0';
	return `Rp ${Math.round(amount).toLocaleString('id-ID')}`;
}

export function formatRupiahShort(value: Amount): string {
	const amount = Number(value);
	if (!Number.isFinite(amount)) return 'Rp 0';
	const abs = Math.abs(amount);
	if (abs >= 1_000_000_000) return `Rp ${(amount / 1_000_000_000).toLocaleString('id-ID', { maximumFractionDigits: 1 })} M`;
	if (abs >= 1_000_000) return `Rp ${(amount / 1_000_000).toLocaleString('id-ID', { maximumFractionDigits: 2 })} jt`;
	if (abs >= 1_000) return `Rp ${(amount / 1_000).toLocaleString('id-ID', { maximumFractionDigits: 0 })} rb`;
	return `Rp ${Math.round(amount).toLocaleString('id-ID')}`;
}

export function formatNumber(value: Amount, maximumFractionDigits = 3): string {
	return Number(value).toLocaleString('id-ID', { maximumFractionDigits });
}

export function formatPercent(value: Amount): string {
	return `${Math.abs(Number(value)).toLocaleString('id-ID', { maximumFractionDigits: 1 })}%`;
}

export function formatAmount(value: Amount): string {
	return Math.round(Number(value)).toLocaleString('id-ID');
}

export function formatSigned(value: Amount): string {
	const amount = Math.round(Number(value));
	return `${amount > 0 ? '+' : ''}${amount.toLocaleString('id-ID')}`;
}

export function formatMillions(value: Amount): string {
	const millions = Math.round((Number(value) / 1_000_000) * 100) / 100;
	if (millions === 0) return '0';
	return `${millions > 0 ? '+' : ''}${millions.toLocaleString('id-ID', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
}

export function formatPercentPlain(value: Amount): string {
	return `${Number(value).toLocaleString('id-ID', { maximumFractionDigits: 1 })}%`;
}

export const EMPTY_VALUE = '—';

export function formatRupiahOrDash(value: Amount | null): string {
	return value === null ? EMPTY_VALUE : formatRupiah(value);
}

export function formatNumberOrDash(value: Amount | null, maximumFractionDigits = 3): string {
	return value === null ? EMPTY_VALUE : formatNumber(value, maximumFractionDigits);
}

export function formatPercentOrDash(value: Amount | null, maximumFractionDigits = 1): string {
	return value === null ? EMPTY_VALUE : `${formatNumber(value, maximumFractionDigits)}%`;
}

/** The whole-rupiah digits of a money input (thousand dots and other characters dropped); empty when there is no digit. */
export function rupiahDigits(text: string): string {
	return text.replace(/\D/g, '');
}

/** The money input text for a stored rupiah value; empty when there is no value yet. */
export function rupiahInput(value: Amount): string {
	return value === null || value === undefined || value === '' ? '' : String(Math.round(Number(value)));
}

/** The whole-rupiah value of a money input; 0 when there is no digit. */
export function rupiahValue(text: string): number {
	return Number(rupiahDigits(text) || '0');
}
