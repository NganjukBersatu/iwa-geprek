/** Warna dari teks hex "#RRGGBB" atau "#RRGGBBAA" (gaya CSS); null bila tidak terbaca. */
export function parseHexColor(hex: string | null | undefined): string | null {
	const digits = hex?.trim().replace(/^#/, '');
	if (!digits || !/^[0-9a-fA-F]+$/.test(digits)) return null;
	return digits.length === 6 || digits.length === 8 ? `#${digits}` : null;
}

/** Terang relatif 0..1 dari warna "#RRGGBB" atau "#RRGGBBAA", sama dengan Color.luminance di Compose (sRGB ke linear). */
export function luminance(hex: string): number {
	const channel = (offset: number) => {
		const value = parseInt(hex.slice(1 + offset * 2, 3 + offset * 2), 16) / 255;
		return value <= 0.03928 ? value / 12.92 : ((value + 0.055) / 1.055) ** 2.4;
	};
	return 0.2126 * channel(0) + 0.7152 * channel(1) + 0.0722 * channel(2);
}
