import type { ChoiceDto, SelfScheduleInDto, SelfScheduleOptionsDto } from '$lib/api/types';
import { current } from '$lib/auth/current.svelte';
import { failureText } from '$lib/failure/failure';
import { stamp, type WibStamp } from '$lib/format/datetime';

const BASE = '/v2/attendance/self-schedule';

/** Langkah absen mandiri: pemberitahuan tidak terdaftar, lalu isian jadwal. */
export type SelfScheduleStep = 'intro' | 'form';

export type SelfScheduleChoice = { id: string; name: string };
export type ShiftSuggestion = { shiftCodeId: string; code: string; startsAt: WibStamp | null; endsAt: WibStamp | null };
export type SelfScheduleOptions = { outlets: SelfScheduleChoice[]; roles: SelfScheduleChoice[]; suggestions: ShiftSuggestion[] };

const choiceOf = (dto: ChoiceDto): SelfScheduleChoice => ({ id: dto.id, name: dto.name });

function optionsOf(dto: SelfScheduleOptionsDto): SelfScheduleOptions {
	return {
		outlets: dto.outlets.map(choiceOf),
		roles: dto.roles.map(choiceOf),
		suggestions: dto.suggestions.map((item) => ({ shiftCodeId: item.shift_code_id, code: item.code, startsAt: stamp(item.starts_at), endsAt: stamp(item.ends_at) }))
	};
}

/** Jadwal yang dibuat karyawan sendiri saat tidak punya jadwal hari ini; setelah itu absen datang berjalan biasa. */
export class SelfScheduleState {
	step = $state<SelfScheduleStep | null>(null);
	options = $state<SelfScheduleOptions | null>(null);
	loading = $state(false);
	outletId = $state<string | null>(null);
	roleId = $state<string | null>(null);
	shiftCodeId = $state<string | null>(null);
	reason = $state('');
	submitting = $state(false);
	error = $state<string | null>(null);

	readonly canSubmit = $derived(this.outletId !== null && this.roleId !== null && this.shiftCodeId !== null && !this.loading);

	private token = 0;

	constructor(private readonly onSessionExpired: () => void) {}

	private reset(step: SelfScheduleStep | null): void {
		this.token += 1;
		this.step = step;
		this.options = null;
		this.loading = false;
		this.outletId = null;
		this.roleId = null;
		this.shiftCodeId = null;
		this.reason = '';
		this.submitting = false;
		this.error = null;
	}

	start(): void {
		this.reset('intro');
	}

	close(): void {
		this.reset(null);
	}

	/** Membuka isian dan memuat cabang serta peran. */
	openForm(): void {
		this.step = 'form';
		void this.load(null);
	}

	/** Ganti cabang mengosongkan kode shift karena saran kode milik cabang. */
	selectOutlet(outletId: string | null): void {
		if (outletId === this.outletId) return;
		this.outletId = outletId;
		this.shiftCodeId = null;
		this.error = null;
		void this.load(outletId);
	}

	selectRole(roleId: string | null): void {
		this.roleId = roleId;
		this.error = null;
	}

	selectShift(shiftCodeId: string): void {
		this.shiftCodeId = shiftCodeId;
		this.error = null;
	}

	/** Menyimpan jadwal; [onCreated] menerima id jadwal baru untuk absen datang. */
	async submit(onCreated: (scheduleId: string) => void): Promise<void> {
		if (this.submitting || !this.canSubmit || !this.outletId || !this.roleId || !this.shiftCodeId) return;
		const body: SelfScheduleInDto = { outlet_id: this.outletId, role_id: this.roleId, shift_code_id: this.shiftCodeId, reason: this.reason.trim() || null };
		this.submitting = true;
		this.error = null;
		const result = await current.api().write<{ id: string }>('POST', BASE, body);
		if (result.kind === 'unauthorized') return this.onSessionExpired();
		if (result.kind === 'failure') {
			this.submitting = false;
			this.error = failureText(result.failure);
			return;
		}
		this.reset(null);
		onCreated(result.value.id);
	}

	private async load(outletId: string | null): Promise<void> {
		const token = ++this.token;
		this.loading = true;
		this.error = null;
		const result = await current.api().read<SelfScheduleOptionsDto>(`${BASE}/options`, { outlet_id: outletId });
		if (token !== this.token) return;
		if (result.kind === 'unauthorized') return this.onSessionExpired();
		this.loading = false;
		if (result.kind === 'success') this.options = optionsOf(result.value);
		else this.error = failureText(result.failure);
	}
}
