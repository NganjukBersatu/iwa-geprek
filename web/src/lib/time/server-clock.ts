/** The one source of "now" in the management web: the server's clock from the `Date` header of API replies, the device clock until the first reply. */
let offsetMillis = 0;

export const ServerClock = {
	nowMillis(): number {
		return Date.now() + offsetMillis;
	},

	now(): Date {
		return new Date(this.nowMillis());
	},

	/** An RFC 1123 date such as "Wed, 14 Oct 2026 08:00:00 GMT"; anything unreadable is ignored. */
	sync(httpDate: string | null): void {
		if (!httpDate) return;
		const millis = Date.parse(httpDate);
		if (Number.isNaN(millis)) return;
		offsetMillis = millis - Date.now();
	}
};
