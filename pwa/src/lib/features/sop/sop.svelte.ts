import { current } from '$lib/auth/current.svelte';
import type { AppFailure } from '$lib/failure/failure';

export type SopSummary = { id: string; title: string; version: number; slideCount: number };
export type SopDocument = { id: string; title: string; version: number; slides: { title: string; body: string }[] };

type SummaryResponse = { id: string; title: string; version: number; slide_count: number };
type DetailResponse = SummaryResponse & { slides: { title: string; body: string }[] };
type ReadResponse = { sop_id: string; version: number };

/** Tanda selesai membaca yang belum diterima server, disimpan untuk dikirim ulang. */
type PendingRead = { sopId: string; version: number };

/** Keadaan halaman Prosedur Kerja: daftar SOP, tanda versi baru dari server, dan SOP yang sedang dibaca. */
export class SopState {
	loading = $state(true);
	failure = $state<AppFailure | null>(null);
	items = $state<SopSummary[]>([]);
	/** Versi tiap SOP yang sudah diselesaikan sampai slide terakhir, dari server. */
	read = $state<Record<string, number>>({});
	opening = $state(false);
	openFailure = $state<AppFailure | null>(null);
	opened = $state<SopDocument | null>(null);
	pendingRead = $state<PendingRead | null>(null);
	readFailure = $state<AppFailure | null>(null);

	constructor(private readonly onSessionExpired: () => void) {}

	isNew(item: SopSummary): boolean {
		return (this.read[item.id] ?? 0) < item.version;
	}

	async load(): Promise<void> {
		this.loading = true;
		this.failure = null;
		const api = current.api();
		const [listed, marked] = await Promise.all([api.read<SummaryResponse[]>('/v2/sop'), api.read<ReadResponse[]>('/v2/sop/reads')]);
		if (listed.kind === 'unauthorized' || marked.kind === 'unauthorized') return this.onSessionExpired();
		this.loading = false;
		if (listed.kind === 'failure') {
			this.failure = listed.failure;
			return;
		}
		if (marked.kind === 'failure') {
			this.failure = marked.failure;
			return;
		}
		this.items = listed.value.map((dto) => ({ id: dto.id, title: dto.title, version: dto.version, slideCount: dto.slide_count }));
		this.read = Object.fromEntries(marked.value.map((dto) => [dto.sop_id, dto.version]));
	}

	async open(item: SopSummary): Promise<void> {
		if (this.opening) return;
		this.opening = true;
		this.openFailure = null;
		const result = await current.api().read<DetailResponse>(`/v2/sop/${item.id}`);
		if (result.kind === 'unauthorized') return this.onSessionExpired();
		this.opening = false;
		if (result.kind === 'failure') {
			this.openFailure = result.failure;
			return;
		}
		const dto = result.value;
		this.opened = { id: dto.id, title: dto.title, version: dto.version, slides: dto.slides.map((slide) => ({ title: slide.title, body: slide.body })) };
	}

	/** Keluar sebelum slide terakhir tidak dihitung membaca. */
	close(): void {
		this.opened = null;
	}

	/** Slide terakhir selesai: tanda Baru langsung hilang, lalu tandanya dikirim ke server. */
	finish(): void {
		const document = this.opened;
		if (!document) return;
		this.opened = null;
		this.read = { ...this.read, [document.id]: Math.max(this.read[document.id] ?? 0, document.version) };
		void this.send({ sopId: document.id, version: document.version });
	}

	retryRead(): void {
		if (this.pendingRead) void this.send(this.pendingRead);
	}

	private async send(pending: PendingRead): Promise<void> {
		this.pendingRead = pending;
		this.readFailure = null;
		const result = await current.api().write('PUT', `/v2/sop/${pending.sopId}/read`, { version: pending.version });
		if (result.kind === 'unauthorized') return this.onSessionExpired();
		if (result.kind === 'failure') {
			this.readFailure = result.failure;
			return;
		}
		this.pendingRead = null;
	}
}
