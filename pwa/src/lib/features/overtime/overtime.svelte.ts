import { current } from '$lib/auth/current.svelte';
import type { AppFailure } from '$lib/failure/failure';
import { failureText } from '$lib/failure/failure';
import { stamp, wibIso, type WibStamp } from '$lib/format/datetime';

const OVERTIME = '/v2/overtime';
export const OVERTIME_PAGE_SIZE = 10;

export type OvertimeEntry = {
	id: string;
	start: WibStamp | null;
	end: WibStamp | null;
	minutes: number;
	/** True untuk lembur dari jadwal; false untuk yang dicatat sendiri. */
	scheduled: boolean;
	note: string | null;
};

/** Lembur dadakan yang diisi karyawan: mulai dan selesai bertanggal (WIB), serta alasan. */
export type OvertimeRequest = { startDate: string; startTime: string; endDate: string; endTime: string; note: string };

type OvertimeResponse = { id: string; started_at?: string | null; ended_at?: string | null; minutes?: number; scheduled?: boolean; note?: string | null };

const entryOf = (dto: OvertimeResponse): OvertimeEntry => ({
	id: dto.id,
	start: stamp(dto.started_at),
	end: stamp(dto.ended_at),
	minutes: dto.minutes ?? 0,
	scheduled: dto.scheduled ?? false,
	note: dto.note?.trim() ? dto.note : null
});

/** Keadaan bagian lembur: riwayat bulan ini dan pencatatan lembur dadakan. */
export class OvertimeState {
	entries = $state<OvertimeEntry[]>([]);
	/** Halaman riwayat berbasis nol. */
	page = $state(0);
	loading = $state(true);
	failure = $state<AppFailure | null>(null);
	/** Sedang menyimpan lembur dadakan. */
	working = $state(false);
	error = $state<string | null>(null);

	constructor(private readonly onSessionExpired: () => void) {}

	get pageCount(): number {
		return Math.ceil(this.entries.length / OVERTIME_PAGE_SIZE);
	}

	get pageEntries(): OvertimeEntry[] {
		return this.entries.slice(this.page * OVERTIME_PAGE_SIZE, (this.page + 1) * OVERTIME_PAGE_SIZE);
	}

	async load(): Promise<void> {
		this.loading = this.entries.length === 0;
		this.failure = null;
		const result = await current.api().read<OvertimeResponse[]>(`${OVERTIME}/mine`);
		if (result.kind === 'unauthorized') return this.onSessionExpired();
		this.loading = false;
		if (result.kind === 'success') {
			this.entries = result.value.map(entryOf);
			this.page = 0;
		} else {
			this.failure = result.failure;
		}
	}

	setPage(page: number): void {
		this.page = Math.min(Math.max(page, 0), Math.max(this.pageCount - 1, 0));
	}

	/** Menyimpan lembur dadakan; mengembalikan true bila berhasil. */
	async record(request: OvertimeRequest): Promise<boolean> {
		if (this.working) return false;
		this.working = true;
		this.error = null;
		const result = await current.api().write('POST', OVERTIME, {
			started_at: wibIso(request.startDate, request.startTime),
			ended_at: wibIso(request.endDate, request.endTime),
			note: request.note.trim()
		});
		if (result.kind === 'unauthorized') {
			this.onSessionExpired();
			return false;
		}
		this.working = false;
		if (result.kind === 'failure') {
			this.error = failureText(result.failure);
			return false;
		}
		void this.load();
		return true;
	}

	clearError(): void {
		this.error = null;
	}
}
