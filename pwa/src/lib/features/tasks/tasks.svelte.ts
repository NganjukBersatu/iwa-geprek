import { current } from '$lib/auth/current.svelte';
import type { PickedMedia, RemoteAttachment } from '$lib/components/media/types';
import { cancelRun, completeBatch, deleteRun, fixRun, sentAnswers, todayBatches, type Batch, type BatchAnswer, type SentAnswer } from '$lib/features/batches/batches';
import type { ApiResult } from '$lib/api/http';
import { failureText, type AppFailure } from '$lib/failure/failure';
import { daysAgo, stamp, todayWib, type WibStamp } from '$lib/format/datetime';
import { ServerClock } from '$lib/time/server-clock';

const TASKS = '/v2/tasks';
export const TASK_PAGE_SIZE = 10;
const WEEK_DAYS = 7;
const SEARCH_DEBOUNCE_MILLIS = 400;
const VIDEO_KIND = 'video';

export type TaskFilter = 'belum' | 'selesai';
/** Rentang tanggal daftar tugas; "bulan ini" tidak mengirim tanggal sehingga server memakai bawaannya. */
export type TaskPeriod = 'month' | 'today' | 'week' | 'custom';
export type TaskItem = {
	id: string;
	title: string;
	description: string | null;
	outletName: string | null;
	/** Pemberi tugas; null bila akunnya sudah tidak ada. */
	creatorName: string | null;
	assigneeName: string | null;
	due: WibStamp | null;
	done: boolean;
	doneNote: string | null;
	doneAt: WibStamp | null;
	/** Pengisian tugas rutin atau outlet yang ditindaklanjuti tugas ini, beserta urutannya; null untuk tugas biasa. */
	followUp: { name: string; day: string; number: number; total: number } | null;
	attachments: RemoteAttachment[];
	/** Diberikan kepada orang yang membuka daftar. */
	mine: boolean;
	canEdit: boolean;
	canComplete: boolean;
	/** Tugas yang sudah selesai boleh dibetulkan catatan dan buktinya oleh pengirimnya. */
	canFix: boolean;
	canDelete: boolean;
};

export type TaskPerson = { id: string; name: string };
/** Pilihan untuk formulir tugas: cabang yang boleh dipilih dan karyawan yang boleh diberi tugas. */
export type TaskOptions = { outlets: TaskPerson[]; assignees: TaskPerson[]; canManage: boolean };

/** Isi formulir tugas baru; [due] sudah berformat ISO dengan zona waktu, atau null bila tanpa batas waktu. */
export type NewTask = { title: string; description: string; assigneeId: string | null; due: string | null; complete: boolean; media: PickedMedia[] };

type PersonResponse = { id: string; name?: string | null; username?: string };
type TaskResponse = {
	id: string;
	status: string;
	title: string;
	description?: string | null;
	outlet?: { id: string; name: string } | null;
	assignee?: PersonResponse | null;
	creator?: PersonResponse | null;
	due_at?: string | null;
	completion_note?: string | null;
	completed_at?: string | null;
	attachments?: { id: string; kind: string; url: string; removable?: boolean }[];
	mine?: boolean;
	can_edit?: boolean;
	can_complete?: boolean;
	can_fix?: boolean;
	can_delete?: boolean;
	source_run?: { batch_name: string; day: string } | null;
	follow_up_number?: number | null;
	follow_up_total?: number | null;
};

const labelOf = (person: PersonResponse | null | undefined): string | null => (person ? person.name?.trim() || person.username || '' : null);

const taskOf = (dto: TaskResponse): TaskItem => ({
	id: dto.id,
	title: dto.title,
	description: dto.description?.trim() ? dto.description : null,
	outletName: dto.outlet?.name ?? null,
	creatorName: labelOf(dto.creator),
	assigneeName: labelOf(dto.assignee),
	due: stamp(dto.due_at),
	done: dto.status === 'selesai',
	doneNote: dto.completion_note?.trim() ? dto.completion_note : null,
	doneAt: stamp(dto.completed_at),
	followUp: dto.source_run ? { name: dto.source_run.batch_name, day: dto.source_run.day, number: dto.follow_up_number ?? 1, total: dto.follow_up_total ?? 1 } : null,
	attachments: (dto.attachments ?? []).map((item) => ({ id: item.id, isVideo: item.kind === VIDEO_KIND, url: item.url, removable: item.removable ?? false })),
	mine: dto.mine ?? false,
	canEdit: dto.can_edit ?? false,
	canComplete: dto.can_complete ?? false,
	canFix: dto.can_fix ?? false,
	canDelete: dto.can_delete ?? dto.can_edit ?? false
});

function mediaForm(media: readonly PickedMedia[], form = new FormData()): FormData {
	media.forEach((item) => form.append('files', item.blob, item.fileName));
	return form;
}

/** Keadaan halaman Tugas: penyaring, daftar berhalaman, tugas outlet hari ini, dan perubahan tugas. */
export class TasksState {
	filter = $state<TaskFilter>('belum');
	/** Rentang tanggal yang dilihat; bawaannya bulan ini. */
	period = $state<TaskPeriod>('month');
	/** Rentang pilihan sendiri; hanya berlaku saat [period] adalah custom. */
	customFrom = $state('');
	customTo = $state('');
	/** Kata yang dicari di judul, isi, dan nama orang. */
	search = $state('');
	/** Hanya tugas yang diberikan ke orang ini; null berarti siapa pun. */
	assigneeId = $state<string | null>(null);
	/** Cabang yang disaring; null berarti semua cabang yang boleh dilihat. */
	outletId = $state<string | null>(null);
	/** Halaman berbasis nol. */
	page = $state(0);
	items = $state<TaskItem[]>([]);
	total = $state(0);
	loading = $state(true);
	failure = $state<AppFailure | null>(null);
	options = $state<TaskOptions | null>(null);
	/** Sedang mengirim perubahan tugas. */
	submitting = $state(false);
	submitError = $state<string | null>(null);
	/** Tugas outlet hari ini untuk orang ini; kosong bila belum absen dalam rentang waktunya. */
	batches = $state<Batch[]>([]);
	batchSubmitting = $state(false);
	batchError = $state<string | null>(null);

	private token = 0;
	private searchTimer: ReturnType<typeof setTimeout> | undefined;

	constructor(private readonly onSessionExpired: () => void) {
		const today = todayWib(ServerClock.nowEpochSeconds());
		this.customFrom = today;
		this.customTo = today;
		void this.loadOptions(null);
	}

	get pageCount(): number {
		return Math.ceil(this.total / TASK_PAGE_SIZE);
	}

	private get dateFrom(): string | null {
		const now = ServerClock.nowEpochSeconds();
		if (this.period === 'today') return todayWib(now);
		if (this.period === 'week') return daysAgo(now, WEEK_DAYS - 1);
		if (this.period === 'custom') return this.customFrom;
		return null;
	}

	private get dateTo(): string | null {
		if (this.period === 'today' || this.period === 'week') return todayWib(ServerClock.nowEpochSeconds());
		if (this.period === 'custom') return this.customTo;
		return null;
	}

	/** Tugas outlet dan rutin hari ini yang lolos saringan layar: nama memuat kata cari, saringan orang bukan orang lain, dan rentang tanggal memuat hari ini. */
	matchingBatches(ownUserId: string): Batch[] {
		const today = todayWib(ServerClock.nowEpochSeconds());
		const from = this.dateFrom;
		const to = this.dateTo;
		const otherPerson = this.assigneeId !== null && this.assigneeId !== ownUserId;
		const outsideRange = (from !== null && today < from) || (to !== null && today > to);
		if (otherPerson || outsideRange) return [];
		const word = this.search.trim().toLowerCase();
		return word === '' ? this.batches : this.batches.filter((batch) => batch.name.toLowerCase().includes(word));
	}

	/** Jumlah penyaring yang dipilih selain status dan kata pencarian, untuk lencana tombol filter. */
	get activeFilterCount(): number {
		return [this.period !== 'month', this.assigneeId !== null, this.outletId !== null].filter(Boolean).length;
	}

	setFilter(filter: TaskFilter): void {
		if (filter === this.filter) return;
		this.filter = filter;
		this.page = 0;
		void this.load();
	}

	setPeriod(period: TaskPeriod): void {
		if (period === this.period) return;
		this.period = period;
		this.page = 0;
		void this.load();
	}

	setCustomRange(from: string, to: string): void {
		this.period = 'custom';
		this.customFrom = from;
		this.customTo = to;
		this.page = 0;
		void this.load();
	}

	/** Kata pencarian langsung berlaku; pemuatan menunggu sebentar agar tidak berjalan di setiap ketukan huruf. */
	setSearch(search: string): void {
		this.search = search;
		this.page = 0;
		clearTimeout(this.searchTimer);
		this.searchTimer = setTimeout(() => void this.load(), SEARCH_DEBOUNCE_MILLIS);
	}

	setAssignee(assigneeId: string | null): void {
		if (assigneeId === this.assigneeId) return;
		this.assigneeId = assigneeId;
		this.page = 0;
		void this.load();
	}

	/** Mengembalikan tanggal, orang, dan cabang ke bawaan; kata pencarian dan status tetap. */
	resetFilters(): void {
		this.period = 'month';
		this.assigneeId = null;
		this.outletId = null;
		this.page = 0;
		void this.load();
	}

	setOutlet(outletId: string | null): void {
		if (outletId === this.outletId) return;
		this.outletId = outletId;
		this.page = 0;
		void this.load();
	}

	setPage(page: number): void {
		this.page = Math.min(Math.max(page, 0), Math.max(this.pageCount - 1, 0));
		void this.load();
	}

	async load(): Promise<void> {
		const token = ++this.token;
		this.loading = true;
		this.failure = null;
		const result = await current.api().read<{ items?: TaskResponse[]; total?: number }>(TASKS, {
			status: this.filter,
			date_from: this.dateFrom,
			date_to: this.dateTo,
			outlet_id: this.outletId,
			assignee_id: this.assigneeId,
			q: this.search.trim() || null,
			page: this.page + 1,
			size: TASK_PAGE_SIZE
		});
		if (token !== this.token) return;
		if (result.kind === 'unauthorized') return this.onSessionExpired();
		this.loading = false;
		if (result.kind === 'failure') {
			this.failure = result.failure;
			return;
		}
		this.items = (result.value.items ?? []).map(taskOf);
		this.total = result.value.total ?? 0;
	}

	/** Memuat karyawan yang boleh diberi tugas di [outletId]; null memakai cabang akun ini. */
	async loadOptions(outletId: string | null): Promise<void> {
		const result = await current.api().read<{ outlets?: PersonResponse[]; assignees?: PersonResponse[]; can_manage?: boolean }>(`${TASKS}/options`, { outlet_id: outletId });
		if (result.kind === 'unauthorized') return this.onSessionExpired();
		if (result.kind !== 'success') return;
		const value = result.value;
		this.options = {
			outlets: (value.outlets ?? []).map((outlet) => ({ id: outlet.id, name: outlet.name ?? '' })),
			assignees: (value.assignees ?? []).map((person) => ({ id: person.id, name: labelOf(person) ?? '' })),
			canManage: value.can_manage ?? false
		};
	}

	/** Gagal memuat tugas outlet tidak menggagalkan halaman; kartunya hanya tidak tampil. */
	async loadBatches(): Promise<void> {
		const result = await todayBatches();
		if (result.kind === 'unauthorized') return this.onSessionExpired();
		if (result.kind === 'success') this.batches = result.value;
	}

	async completeBatch(batchId: string, answers: readonly BatchAnswer[]): Promise<boolean> {
		if (this.batchSubmitting) return false;
		this.batchSubmitting = true;
		this.batchError = null;
		const result = await completeBatch(batchId, answers);
		if (result.kind === 'unauthorized') {
			this.onSessionExpired();
			return false;
		}
		this.batchSubmitting = false;
		if (result.kind === 'failure') {
			this.batchError = failureText(result.failure);
			return false;
		}
		void this.loadBatches();
		return true;
	}

	/** Jawaban yang sudah dikirim untuk form perbaikan; null bila gagal dimuat, dengan pesannya di [batchError]. */
	async loadSentAnswers(runId: string): Promise<SentAnswer[] | null> {
		if (this.batchSubmitting) return null;
		this.batchSubmitting = true;
		this.batchError = null;
		const result = await sentAnswers(runId);
		this.batchSubmitting = false;
		if (result.kind === 'unauthorized') {
			this.onSessionExpired();
			return null;
		}
		if (result.kind === 'failure') {
			this.batchError = failureText(result.failure);
			return null;
		}
		return result.value;
	}

	fixBatch(runId: string, answers: readonly BatchAnswer[]): Promise<boolean> {
		return this.changeRun(() => fixRun(runId, answers));
	}

	cancelBatch(runId: string): Promise<boolean> {
		return this.changeRun(() => cancelRun(runId));
	}

	deleteBatch(runId: string): Promise<boolean> {
		return this.changeRun(() => deleteRun(runId));
	}

	/** Satu perubahan pada pengisian yang sudah dikirim; kartu dimuat ulang setelah berhasil. */
	private async changeRun(work: () => Promise<ApiResult<null>>): Promise<boolean> {
		if (this.batchSubmitting) return false;
		this.batchSubmitting = true;
		this.batchError = null;
		const result = await work();
		this.batchSubmitting = false;
		if (result.kind === 'unauthorized') {
			this.onSessionExpired();
			return false;
		}
		if (result.kind === 'failure') {
			this.batchError = failureText(result.failure);
			return false;
		}
		void this.loadBatches();
		return true;
	}

	clearBatchError(): void {
		this.batchError = null;
	}

	create(task: NewTask): Promise<boolean> {
		const form = new FormData();
		form.append('title', task.title.trim());
		if (task.description.trim()) form.append('description', task.description.trim());
		if (task.assigneeId) form.append('assignee_id', task.assigneeId);
		if (task.due) form.append('due_at', task.due);
		form.append('complete', String(task.complete));
		mediaForm(task.media, form);
		return this.submit(
			() => current.api().write('POST', TASKS, form),
			() => {
				// Tugas yang langsung diselesaikan tampil di daftar Selesai bulan ini.
				if (task.complete) {
					this.filter = 'selesai';
					this.period = 'month';
					this.page = 0;
				}
			}
		);
	}

	update(taskId: string, title: string, description: string, due: string | null): Promise<boolean> {
		return this.submit(() => current.api().write('PATCH', `${TASKS}/${taskId}`, { title: title.trim(), description: description.trim(), due_at: due }));
	}

	complete(taskId: string, note: string, media: readonly PickedMedia[]): Promise<boolean> {
		const form = new FormData();
		if (note.trim()) form.append('note', note.trim());
		return this.submit(() => current.api().write('POST', `${TASKS}/${taskId}/complete`, mediaForm(media, form)));
	}

	/** Mengganti catatan selesai tugas yang sudah dikirim; buktinya diubah lewat lampiran. */
	fixNote(taskId: string, note: string): Promise<boolean> {
		return this.submit(() => current.api().write('PATCH', `${TASKS}/${taskId}/completion`, { note: note.trim() }));
	}

	addAttachments(taskId: string, media: readonly PickedMedia[]): Promise<boolean> {
		return this.submit(() => current.api().write('POST', `${TASKS}/${taskId}/attachments`, mediaForm(media)));
	}

	removeAttachment(taskId: string, attachmentId: string): Promise<boolean> {
		return this.submit(() => current.api().write('DELETE', `${TASKS}/${taskId}/attachments/${attachmentId}`));
	}

	delete(taskId: string): Promise<boolean> {
		return this.submit(() => current.api().write('DELETE', `${TASKS}/${taskId}`));
	}

	clearSubmitError(): void {
		this.submitError = null;
	}

	private async submit(send: () => Promise<{ kind: string; failure?: AppFailure }>, afterSuccess: () => void = () => undefined): Promise<boolean> {
		if (this.submitting) return false;
		this.submitting = true;
		this.submitError = null;
		const result = await send();
		if (result.kind === 'unauthorized') {
			this.onSessionExpired();
			return false;
		}
		this.submitting = false;
		if (result.kind === 'failure' && result.failure) {
			this.submitError = failureText(result.failure);
			return false;
		}
		afterSuccess();
		void this.load();
		return true;
	}
}
