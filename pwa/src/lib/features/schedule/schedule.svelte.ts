import { current } from '$lib/auth/current.svelte';
import type { AppFailure } from '$lib/failure/failure';
import { firstDay, monthKey, monthOf, nextMonth, previousMonth, sameMonth, todayWib, type YearMonth } from '$lib/format/datetime';
import { parseHexColor } from '$lib/theme/hex';
import { ServerClock } from '$lib/time/server-clock';

export type ShiftCode = {
	id: string;
	code: string;
	/** Nama kategori kode, misalnya nama sesi kerja. */
	category: string | null;
	/** Jam "HH:MM"; kosong untuk kode libur. */
	start: string | null;
	end: string | null;
	/** Jendela lembur "HH:MM", bila kode memilikinya. */
	overtimeStart: string | null;
	overtimeEnd: string | null;
	/** Warna hex pilihan admin. */
	color: string | null;
	off: boolean;
};

export type ScheduleItem = {
	/** Tanggal "YYYY-MM-DD". */
	date: string;
	code: ShiftCode | null;
	/** Penugasan peran pada hari itu. */
	roleName: string | null;
	note: string | null;
	off: boolean;
	userId: string;
	userName: string;
	/** Milik pengguna yang sedang masuk. */
	mine: boolean;
};

type BoardResponse = {
	outlet_name?: string | null;
	assignments?: { date: string; user_id: string; user_username?: string; shift_code_id?: string | null; role_name?: string | null; note?: string | null }[];
	days_off?: { date: string; user_id: string; user_username?: string; shift_code_id?: string | null; note?: string | null }[];
	shift_codes?: {
		id: string;
		code: string;
		category?: string | null;
		start_clock?: string | null;
		end_clock?: string | null;
		overtime_start_clock?: string | null;
		overtime_end_clock?: string | null;
		color?: string | null;
		is_day_off?: boolean;
	}[];
};

function itemsOf(board: BoardResponse, userId: string): ScheduleItem[] {
	const codes = new Map<string, ShiftCode>(
		(board.shift_codes ?? []).map((dto): [string, ShiftCode] => [
			dto.id,
			{
				id: dto.id,
				code: dto.code,
				category: dto.category?.trim() || null,
				start: dto.start_clock ?? null,
				end: dto.end_clock ?? null,
				overtimeStart: dto.overtime_start_clock ?? null,
				overtimeEnd: dto.overtime_end_clock ?? null,
				color: dto.color ?? null,
				off: dto.is_day_off ?? false
			}
		])
	);
	const assignments = (board.assignments ?? []).map((shift): ScheduleItem => {
		const code = shift.shift_code_id ? (codes.get(shift.shift_code_id) ?? null) : null;
		return { date: shift.date, code, roleName: shift.role_name ?? null, note: shift.note ?? null, off: code?.off === true, userId: shift.user_id, userName: shift.user_username ?? '', mine: shift.user_id === userId };
	});
	const daysOff = (board.days_off ?? []).map((off): ScheduleItem => {
		const code = off.shift_code_id ? (codes.get(off.shift_code_id) ?? null) : null;
		return { date: off.date, code, roleName: null, note: off.note ?? null, off: true, userId: off.user_id, userName: off.user_username ?? '', mine: off.user_id === userId };
	});
	return [...assignments, ...daysOff].sort((a, b) => a.date.localeCompare(b.date));
}

/** Keadaan halaman Jadwal: bulan yang dilihat, tanggal terpilih, dan jadwal seluruh staf pada bulan itu. */
export class ScheduleState {
	month = $state<YearMonth>({ year: 0, month: 1 });
	/** Tanggal hari ini "YYYY-MM-DD" menurut jam server (WIB). */
	today = $state('');
	/** Tanggal terpilih "YYYY-MM-DD". */
	selected = $state('');
	/** Jadwal seluruh staf pada [month]. */
	items = $state<ScheduleItem[]>([]);
	loading = $state(true);
	failure = $state<AppFailure | null>(null);
	/** Cabang tempat jadwal berlaku; null selama belum diketahui. */
	outletName = $state<string | null>(null);
	/** Hanya jadwal milik pengguna; kalender mewarnai tanggalnya sesuai kode. */
	onlyMine = $state(false);

	private token = 0;

	constructor(private readonly onSessionExpired: () => void) {
		const today = todayWib(ServerClock.nowEpochSeconds());
		this.today = today;
		this.selected = today;
		this.month = monthOf(today);
	}

	private get visible(): ScheduleItem[] {
		return this.onlyMine ? this.items.filter((item) => item.mine) : this.items;
	}

	/** Bulan berikutnya hanya sampai satu bulan setelah bulan berjalan. */
	get canGoNext(): boolean {
		return !sameMonth(this.month, nextMonth(monthOf(this.today)));
	}

	/** Jadwal pada tanggal terpilih: milik sendiri lebih dulu, lalu menurut jam dan nama. */
	get dayItems(): ScheduleItem[] {
		return this.visible
			.filter((item) => item.date === this.selected)
			.sort((a, b) => Number(!a.mine) - Number(!b.mine) || (a.code?.start ?? '99:99').localeCompare(b.code?.start ?? '99:99') || a.userName.localeCompare(b.userName));
	}

	get markers(): Record<string, (string | null)[]> {
		if (this.onlyMine) return {};
		const result: Record<string, (string | null)[]> = {};
		for (const item of this.items) {
			const color = parseHexColor(item.code?.color);
			const list = (result[item.date] ??= []);
			if (!list.includes(color)) list.push(color);
		}
		return result;
	}

	/** Warna blok per tanggal untuk jadwal milik sendiri; kosong bila filter mati. */
	get fills(): Record<string, string> {
		const result: Record<string, string> = {};
		if (!this.onlyMine) return result;
		for (const item of this.visible) {
			const color = parseHexColor(item.code?.color);
			if (color) result[item.date] = color;
		}
		return result;
	}

	/** Tanggal bertugas milik sendiri; berdenyut di kalender hanya selama filter "Jadwal saya" mati. */
	get pulses(): Record<string, string | null> {
		const result: Record<string, string | null> = {};
		if (this.onlyMine) return result;
		for (const item of this.items) if (item.mine && !item.off) result[item.date] = parseHexColor(item.code?.color);
		return result;
	}

	/** Kode yang dipakai pada bulan ini, untuk keterangan. */
	get codes(): ShiftCode[] {
		const unique = new Map<string, ShiftCode>();
		for (const item of this.items) if (item.code) unique.set(item.code.id, item.code);
		return [...unique.values()].sort((a, b) => a.code.localeCompare(b.code));
	}

	previousMonth(): void {
		this.changeMonth(previousMonth(this.month));
	}

	nextMonth(): void {
		if (this.canGoNext) this.changeMonth(nextMonth(this.month));
	}

	toggleOnlyMine(): void {
		this.onlyMine = !this.onlyMine;
	}

	select(date: string): void {
		this.selected = date;
	}

	async load(): Promise<void> {
		const token = ++this.token;
		this.loading = true;
		this.failure = null;
		const userId = current.session?.user.id ?? '';
		const result = await current.api().read<BoardResponse>('/v2/schedule/month', { month: monthKey(this.month) });
		if (token !== this.token) return;
		if (result.kind === 'unauthorized') return this.onSessionExpired();
		if (result.kind === 'failure') {
			this.loading = false;
			this.failure = result.failure;
			return;
		}
		this.items = itemsOf(result.value, userId);
		this.outletName = result.value.outlet_name ?? this.outletName;
		this.loading = false;
		this.today = todayWib(ServerClock.nowEpochSeconds());
	}

	private changeMonth(month: YearMonth): void {
		this.selected = sameMonth(monthOf(this.today), month) ? this.today : firstDay(month);
		this.month = month;
		this.items = [];
		void this.load();
	}
}
