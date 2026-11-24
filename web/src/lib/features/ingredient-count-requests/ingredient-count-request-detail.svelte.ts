import { goto } from '$app/navigation';
import { api } from '$lib/api';
import { userMessage } from '$lib/api/user-message';
import type { IngredientClosingPeriod, IngredientCountRequest, StockReport } from '$lib/api/types';
import { toast } from '$lib/components/feedback/toast.svelte';
import { formatTime } from '$lib/format/datetime';
import { numberInput, parseNumber } from '$lib/format/number';
import { ingredientCountPath, PAGES } from '$lib/nav/pages';
import { controlText } from '$lib/text/controls';
import { ingredientCountRequestText as text } from '$lib/text/ingredient-count-requests';

/** Typing is saved as a draft this long after the last keystroke, same delay as the branch sheet uses. */
const DRAFT_DELAY_MILLIS = 700;

/** One pending request to close a branch period: its context, the live sheet from its start to today, and the two decisions an admin can make on it. */
export class IngredientCountRequestDetailState {
	request = $state<IngredientCountRequest | null>(null);
	sheet = $state<StockReport | null>(null);
	/** Rentang yang akan ditutup, dari server; sama dengan pilihan otomatis di halaman Stok Opname. */
	period = $state<IngredientClosingPeriod | null>(null);
	loading = $state(true);
	error = $state('');
	busy = $state(false);
	actionError = $state('');
	closing = $state(false);
	rejecting = $state(false);
	counted = $state<Record<string, string>>({});
	draftSavedAt = $state('');
	draftProblem = $state('');

	private dirty = new Set<string>();
	private draftTimer: ReturnType<typeof setTimeout> | undefined;
	private draftLoadedFor = '';

	constructor(readonly id: string) {}

	get rows() {
		return this.sheet?.rows ?? [];
	}

	get filled(): number {
		return Object.values(this.counted).filter((value) => value.trim() !== '').length;
	}

	/** Bahan yang kembali ke 0 saat periode ditutup: yang masih punya stok sistem sekarang. */
	get resetTotal(): number {
		return this.rows.filter((row) => Number(row.closing_stock) !== 0).length;
	}

	get differenceTotal(): number {
		// Stok sistem minus tidak dihitung sebagai selisih, sama dengan halaman opname yang sudah ditutup.
		return this.rows.filter((row) => Number(row.closing_stock) >= 0 && (this.difference(row.ingredient_id, row.closing_stock) ?? 0) !== 0).length;
	}

	/** Difference of one typed count against the book balance; null while nothing is typed. */
	difference(ingredientId: string, closing: string): number | null {
		const typed = this.counted[ingredientId]?.trim();
		if (!typed) return null;
		const value = parseNumber(typed);
		return value === null ? null : value - Number(closing);
	}

	async load(): Promise<void> {
		this.loading = true;
		this.error = '';
		try {
			this.request = await api.ingredientCountRequests.get(this.id);
			await this.loadSheet();
			void this.markSeen();
		} catch (failure) {
			this.error = userMessage(failure, text.loadFailed);
		} finally {
			this.loading = false;
		}
	}

	/** Pengaju melihat bahwa pengajuannya sedang ditinjau; gagal mencatatnya tidak menghalangi admin memutus. */
	private async markSeen(): Promise<void> {
		if (this.request?.status !== 'pending' || this.request.seen_at) return;
		try {
			await api.ingredientCountRequests.markSeen(this.id);
		} catch {
			// Tanda dilihat dicatat ulang saat halaman dibuka lagi.
		}
	}

	/** Reloads quietly after a live signal: what the screen shows stays until the fresh request and sheet arrive. */
	async refresh(): Promise<void> {
		try {
			this.request = await api.ingredientCountRequests.get(this.id);
			await this.loadSheet();
		} catch {
			// The request on screen stays; the next signal or a reload tries again.
		}
	}

	private async loadSheet(): Promise<void> {
		const request = this.request;
		if (!request) return;
		// Rentang mengikuti periode cabang yang harus ditutup, sama dengan penutupan langsung dari halaman Stok Opname.
		const period = await api.ingredientCounts.closingPeriod(request.outlet_id);
		this.period = period;
		this.sheet = await api.ingredientCounts.sheet(request.outlet_id, { start: period.start, end: period.end });
		await this.loadDraft(request.outlet_id);
	}

	/** Brings back what was typed on the branch own sheet screen, without overwriting what is typed here. */
	private async loadDraft(outletId: string): Promise<void> {
		if (this.draftLoadedFor === outletId) return;
		this.draftLoadedFor = outletId;
		try {
			const draft = await api.ingredientCounts.draft(outletId);
			for (const line of draft.lines) {
				if (this.counted[line.ingredient_id] === undefined) this.counted[line.ingredient_id] = numberInput(line.counted);
			}
			if (draft.lines.length > 0) this.draftSavedAt = formatTime(draft.lines.reduce((latest, line) => (line.updated_at > latest ? line.updated_at : latest), ''));
		} catch (failure) {
			this.draftLoadedFor = '';
			this.draftProblem = userMessage(failure, text.draftLoadFailed);
		}
	}

	/** One typed figure: shown now, saved to the draft a moment later. */
	type(ingredientId: string, value: string): void {
		this.counted[ingredientId] = value;
		this.dirty.add(ingredientId);
		clearTimeout(this.draftTimer);
		this.draftTimer = setTimeout(() => void this.flush(), DRAFT_DELAY_MILLIS);
	}

	async flush(): Promise<void> {
		clearTimeout(this.draftTimer);
		const outletId = this.request?.outlet_id;
		if (!outletId || this.dirty.size === 0) return;
		const lines: { ingredient_id: string; counted: string | null }[] = [];
		const sent = [...this.dirty];
		for (const ingredientId of sent) {
			const typed = (this.counted[ingredientId] ?? '').trim();
			if (typed === '') {
				lines.push({ ingredient_id: ingredientId, counted: null });
				continue;
			}
			const value = parseNumber(typed);
			if (value !== null && value >= 0) lines.push({ ingredient_id: ingredientId, counted: String(value) });
		}
		this.dirty.clear();
		if (lines.length === 0) return;
		try {
			await api.ingredientCounts.saveDraft(outletId, { lines });
			this.draftSavedAt = formatTime(new Date().toISOString());
			this.draftProblem = '';
		} catch (failure) {
			for (const ingredientId of sent) this.dirty.add(ingredientId);
			this.draftProblem = userMessage(failure, text.draftNotSaved);
		}
	}

	private async attempt<T>(work: () => Promise<T>, fallback: string): Promise<T | null> {
		this.busy = true;
		this.actionError = '';
		try {
			return await work();
		} catch (failure) {
			this.actionError = userMessage(failure, fallback);
			return null;
		} finally {
			this.busy = false;
		}
	}

	askReject(): void {
		this.actionError = '';
		this.rejecting = true;
	}

	/** Membuka kunci periode cabang lagi tanpa mengubah stok; pengaju langsung melihat Ditolak, jadi selalu lewat konfirmasi. */
	async confirmReject(): Promise<void> {
		const done = await this.attempt(() => api.ingredientCountRequests.reject(this.id), text.rejectFailed);
		if (done === null) return;
		this.rejecting = false;
		toast.show(text.rejected);
		await goto(PAGES.ingredientCounts.path);
	}

	askClose(): void {
		this.actionError = '';
		this.closing = true;
	}

	/** Menutup periode cabang yang harus ditutup, memakai jumlah fisik yang sudah diisi di sini atau di draf cabang. */
	async confirmClose(): Promise<void> {
		const request = this.request;
		const period = this.period;
		if (!request || !period) return;
		const lines: { ingredient_id: string; counted: string }[] = [];
		for (const [ingredientId, typed] of Object.entries(this.counted)) {
			if (!typed.trim()) continue;
			const value = parseNumber(typed);
			if (value === null || value < 0) {
				this.actionError = controlText.countedInvalid;
				return;
			}
			lines.push({ ingredient_id: ingredientId, counted: String(value) });
		}
		const result = await this.attempt(() => api.ingredientCounts.close(request.outlet_id, { start: period.start, end: period.end, note: request.note, lines }), text.closeFailed);
		if (result === null) return;
		this.closing = false;
		toast.show(text.closed);
		await goto(ingredientCountPath(result.id));
	}

	closeDialogs(): void {
		this.closing = false;
		this.rejecting = false;
		this.actionError = '';
	}
}
