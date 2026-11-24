/** Satu-satunya sumber "sekarang": jam server dari header `Date` jawaban API, memakai jam perangkat sampai jawaban pertama. */
let offsetMillis: number | null = null;

export const ServerClock = {
	nowEpochSeconds(): number {
		return Math.floor((Date.now() + (offsetMillis ?? 0)) / 1000);
	},

	/** [httpDate] berformat RFC 1123, contoh "Wed, 14 Oct 2026 08:00:00 GMT"; yang tidak terbaca diabaikan. */
	sync(httpDate: string | null): void {
		if (!httpDate) return;
		const millis = Date.parse(httpDate);
		if (Number.isNaN(millis)) return;
		offsetMillis = millis - Date.now();
	}
};
