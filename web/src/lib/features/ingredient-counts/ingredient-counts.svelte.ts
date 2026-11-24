import { controlText } from '$lib/text/controls';
import { api } from '$lib/api';
import { userMessage } from '$lib/api/user-message';
import type { Ingredient, IngredientCount, IngredientCountRequest, IngredientCountRunning, IngredientOpeningStatus, StockReport } from '$lib/api/types';
import { access } from '$lib/auth/access.svelte';
import { toast } from '$lib/components/feedback/toast.svelte';
import { formatTime } from '$lib/format/datetime';
import { Filters } from '$lib/components/filter/filters.svelte';
import { formatMonthYear, todayIso, type DateRange } from '$lib/date/range';
import { STOCK_TABLES } from '$lib/live/tables';
import { numberInput, parseNumber } from '$lib/format/number';
import { collectPages } from '../manage/collect';
import { ManageState } from '../manage/manage.svelte';
import { reportPresets } from '../report/filters';
import { branchList } from '$lib/stores/branch';
import { memoryKey, recall, remember } from '$lib/stores/memory';
import { ListSort, sortKeys } from '$lib/components/table/list-sort.svelte';
import { historyColumns, sheetColumns, type CountHistoryRow } from './columns';
import { termText } from '$lib/text/terms';
import { ingredientCountText } from '$lib/text/ingredient-counts';

const GUIDE_ID = 'tutup-periode';
const GUIDE_SEEN = 'dilihat';
/** Typing is saved as a draft this long after the last keystroke, so a closed screen or a dead tablet loses at most a moment of it. */
const DRAFT_DELAY_MILLIS = 700;

export type CountQuery = { branch: string | null; range: DateRange | null };

export class IngredientCountsState extends ManageState<IngredientCount> {
	/** Sesi kasir ikut didengar karena menutupnya mengubah syarat penutupan periode. */
	override readonly tables = [...STOCK_TABLES, 'cash_sessions', 'ingredient_counts', 'ingredient_count_lines', 'ingredient_count_requests'];
	readonly sheetSort = new ListSort('opname-lembar', sortKeys(sheetColumns), () => void this.load());
	readonly historySort = new ListSort('opname-riwayat', sortKeys(historyColumns), () => void this.load());

	readonly filters = new Filters([
		{ kind: 'select', key: 'cabang', label: termText.branch, options: [] },
		{ kind: 'date', key: 'rentang', label: termText.period, presets: reportPresets, reach: 'past' },
		{ kind: 'select', key: 'sumber_opname', label: ingredientCountText.source, options: [{ value: 'web', label: ingredientCountText.sourceWeb }, { value: 'tablet', label: ingredientCountText.sourceTablet }] }
	]);

	outlets = $state<{ id: string; name: string }[]>([]);
	/** The branch whose sheet is open: the filter's, or the one picked on the sheet while the list covers every branch. */
	sheetBranch = $state('');
	sheet = $state<StockReport | null>(null);
	counted = $state<Record<string, string>>({});
	note = $state('');
	problem = $state('');
	closing = $state(false);
	/** When the draft was last saved on this screen, and why it could not be. */
	draftSavedAt = $state('');
	draftProblem = $state('');
	running = $state<IngredientCountRunning[]>([]);
	openingOpen = $state(false);
	/** Stok awal periode berjalan cabang di lembar; sama dengan hitungan "Stok awal terisi" di tablet. */
	openingStatus = $state<IngredientOpeningStatus | null>(null);
	/** Pengajuan terakhir periode berjalan cabang di lembar; dibaca pengaju yang tidak bisa menutup sendiri. */
	request = $state<IngredientCountRequest | null>(null);
	requesting = $state(false);
	requestNote = $state('');
	ingredients = $state<Ingredient[]>([]);
	/** Sesi kasir yang masih berjalan sampai tanggal akhir lembar; null selama lembar belum terbuka. */
	openSessions = $state<number | null>(null);
	guideOpen = $state(recall(memoryKey.guide(GUIDE_ID)) !== GUIDE_SEEN);

	/** Bahan di lembar yang stok awal periodenya belum diisi, sehingga Stok Akhir dan Selisihnya dihitung dari 0. */
	get missingOpening(): ReadonlySet<string> {
		return new Set(this.openingStatus?.missing_ids ?? []);
	}

	/** Pemegang stok.opname mengisi jumlah fisik dan menutup; pemegang stok.tutup_periode hanya mengajukan, sama seperti di tablet. */
	get canCount(): boolean {
		return access.allows('count_stock');
	}

	get canRequest(): boolean {
		return !this.canCount && access.allows('request_stock_close');
	}

	/** Rentang lembar sudah tercakup penutupan cabang ini, jadi lembar hanya dibaca: tanpa jumlah fisik, tanpa tutup periode. */
	get settled(): boolean {
		const range = this.query.range;
		const branch = this.branch;
		if (!range || !branch) return false;
		return this.items.some((count) => count.outlet_id === branch && count.end >= range.to);
	}

	/** Halaman ini membuka periode cabang yang harus ditutup, bukan periode yang sedang berjalan. */
	async branchPeriod(branchId: string): Promise<DateRange> {
		const period = await api.ingredientCounts.closingPeriod(branchId);
		return { from: period.start, to: period.end };
	}

	askRequest(): void {
		this.actionError = '';
		this.requestNote = '';
		this.requesting = true;
	}

	async submitRequest(): Promise<void> {
		const branch = this.branch;
		if (!branch) return;
		this.busy = true;
		this.actionError = '';
		try {
			this.request = await api.ingredientCountRequests.submit(branch, this.requestNote.trim() || null);
			this.requesting = false;
			toast.show(ingredientCountText.requestSent);
		} catch (error) {
			this.actionError = userMessage(error, ingredientCountText.requestFailed);
		} finally {
			this.busy = false;
		}
	}

	/** Tombol tidak dimatikan; tanpa satu pun jumlah fisik terisi, pengguna diberi tahu apa yang harus diisi. */
	askClose(): boolean {
		if (this.filled === 0) {
			this.problem = ingredientCountText.countRequiredToClose;
			return false;
		}
		this.problem = '';
		this.closing = true;
		return true;
	}

	get query(): CountQuery {
		return { branch: this.filters.get('cabang'), range: this.filters.range('rentang') };
	}

	/** The branch the sheet, the closing, and the opening balances are written to; empty until one is known. */
	get branch(): string {
		return this.query.branch ?? this.sheetBranch;
	}

	/** The period each branch is in now comes first, then the periods already closed in the order the server gave. */
	get historyRows(): CountHistoryRow[] {
		const pieces = this.running.map<CountHistoryRow>((period) => ({
			key: `${period.state}:${period.outlet_id}:${period.start}`,
			id: null,
			part_start: null,
			running: true,
			state: period.state,
			name: formatMonthYear(period.period_end),
			requested: period.requested,
			outlet_id: period.outlet_id,
			outlet_name: period.outlet_name,
			start: period.start,
			end: period.end ?? null,
			note: null,
			user_name: null,
			source: null,
			ingredient_count: null,
			created_at: null,
			days: period.days
		}));
		const closed = this.items.map<CountHistoryRow>((count) => ({
			key: count.id,
			id: count.id,
			part_start: null,
			running: false,
			state: 'closed',
			name: formatMonthYear(count.end),
			requested: false,
			outlet_id: count.outlet_id,
			outlet_name: count.outlet_name,
			start: count.start,
			end: count.end,
			note: count.note,
			user_name: count.user_name,
			source: count.source,
			ingredient_count: count.ingredient_count,
			created_at: count.created_at,
			days: null
		}));
		const open = pieces.filter((row) => row.state !== 'absorbed');
		// Bagian yang ikut tertutup dibuka di halaman rincian penutupan yang sama, dengan rentang dan angkanya sendiri.
		const absorbed = pieces
			.filter((row) => row.state === 'absorbed')
			.map((row) => {
				const by = closed.filter((count) => count.outlet_id === row.outlet_id && count.start > row.start).sort((a, b) => a.start.localeCompare(b.start))[0];
				return by ? { ...row, id: by.id, part_start: row.start, running: false, user_name: by.user_name, source: by.source, created_at: by.created_at } : row;
			});
		const past = [...closed, ...absorbed].sort((a, b) => b.start.localeCompare(a.start));
		return [...open, ...past];
	}

	private dirty = new Set<string>();
	private draftTimer: ReturnType<typeof setTimeout> | undefined;
	private draftBranch = '';

	/** One typed figure: shown now, saved to the draft a moment later. */
	type(ingredientId: string, text: string): void {
		this.counted[ingredientId] = text;
		this.dirty.add(ingredientId);
		clearTimeout(this.draftTimer);
		this.draftTimer = setTimeout(() => void this.flush(), DRAFT_DELAY_MILLIS);
	}

	/** Saves the figures typed since the last save; one that is not a number yet is left for when it is. */
	async flush(): Promise<void> {
		clearTimeout(this.draftTimer);
		const branch = this.branch;
		if (!branch || this.dirty.size === 0) return;
		const lines: { ingredient_id: string; counted: string | null }[] = [];
		const sent = [...this.dirty];
		for (const ingredientId of sent) {
			const text = (this.counted[ingredientId] ?? '').trim();
			if (text === '') {
				lines.push({ ingredient_id: ingredientId, counted: null });
				continue;
			}
			const value = parseNumber(text);
			if (value !== null && value >= 0) lines.push({ ingredient_id: ingredientId, counted: String(value) });
		}
		this.dirty.clear();
		if (lines.length === 0) return;
		try {
			await api.ingredientCounts.saveDraft(branch, { lines });
			this.draftSavedAt = formatTime(new Date().toISOString());
			this.draftProblem = '';
		} catch (error) {
			for (const ingredientId of sent) this.dirty.add(ingredientId);
			this.draftProblem = userMessage(error, ingredientCountText.draftNotSaved);
		}
	}

	/** Brings back what was typed before on any screen for this branch, without overwriting what is typed here. */
	private async loadDraft(branch: string): Promise<void> {
		if (this.draftBranch === branch) return;
		this.draftBranch = branch;
		try {
			const draft = await api.ingredientCounts.draft(branch);
			for (const line of draft.lines) {
				if (this.counted[line.ingredient_id] === undefined) this.counted[line.ingredient_id] = numberInput(line.counted);
			}
			if (draft.lines.length > 0) this.draftSavedAt = formatTime(draft.lines.reduce((latest, line) => (line.updated_at > latest ? line.updated_at : latest), ''));
		} catch (error) {
			this.draftBranch = '';
			this.draftProblem = userMessage(error, ingredientCountText.draftLoadFailed);
		}
	}

	get filled(): number {
		return Object.values(this.counted).filter((text) => text.trim() !== '').length;
	}

	protected async fetch(): Promise<void> {
		const token = this.token;
		const query = this.query;
		this.outlets = await branchList();
		this.filters.setOptions('cabang', this.outlets.map((outlet) => ({ value: outlet.id, label: outlet.name })));
		[this.items, this.running] = await Promise.all([api.ingredientCounts.list(this.historySort.param, this.filters.get('sumber_opname') ?? undefined), api.ingredientCounts.running()]);
		// Muat yang lebih baru sudah berjalan: hasil lama tidak boleh menimpanya.
		if (token !== this.token) return;
		this.total = this.items.length;
		const branch = this.branch;
		this.sheet = query.range && branch ? await api.ingredientCounts.sheet(branch, { start: query.range.from, end: query.range.to, sort: this.sheetSort.param }) : null;
		this.openSessions = this.sheet && branch && query.range ? (await api.ingredientCounts.openSessions(branch, query.range.to)).count : null;
		this.openingStatus = this.sheet && branch && query.range ? await api.ingredientCounts.openingStatus(branch, query.range.from) : null;
		this.request = this.sheet && branch && this.canRequest ? await api.ingredientCountRequests.current(branch) : null;
		if (this.sheet && branch && this.canCount) await this.loadDraft(branch);
	}

	protected label(count: IngredientCount): string {
		return `${count.start} – ${count.end}`;
	}

	/** Difference of one typed count against the book balance; null while nothing is typed. */
	difference(ingredientId: string, closing: string): number | null {
		const typed = this.counted[ingredientId]?.trim();
		if (!typed) return null;
		const value = parseNumber(typed);
		return value === null ? null : value - Number(closing);
	}

	/** Picking another branch on the sheet starts its typing over. */
	changeSheetBranch(): void {
		this.counted = {};
		this.dirty.clear();
		this.draftBranch = '';
		this.draftSavedAt = '';
		void this.load(true);
	}

	async close(): Promise<void> {
		const range = this.query.range;
		const branch = this.branch;
		if (!range || !branch) return;
		const lines: { ingredient_id: string; counted: string }[] = [];
		for (const [ingredientId, text] of Object.entries(this.counted)) {
			if (!text.trim()) continue;
			const value = parseNumber(text);
			if (value === null || value < 0) {
				this.problem = controlText.countedInvalid;
				return;
			}
			lines.push({ ingredient_id: ingredientId, counted: String(value) });
		}
		if (lines.length === 0) {
			this.problem = ingredientCountText.countedRequired;
			return;
		}
		this.problem = '';
		const done = await this.attempt(() => api.ingredientCounts.close(branch, { start: range.from, end: range.to, note: this.note.trim() || null, lines }), ingredientCountText.closeFailed);
		this.closing = false;
		if (!done) return;
		this.counted = {};
		this.dirty.clear();
		this.draftBranch = '';
		this.draftSavedAt = '';
		this.note = '';
		toast.show(ingredientCountText.closed);
		// Periode yang baru ditutup tidak boleh tetap terpilih; filter pindah ke periode berikutnya menurut aturan yang sama.
		await this.pickClosingPeriod(branch);
		await this.refresh();
	}

	/** Panduan tampil sendiri sekali per akun; setelah disembunyikan, hanya dibuka lewat tombol Panduan. */
	showGuide(open: boolean): void {
		this.guideOpen = open;
		if (!open) remember(memoryKey.guide(GUIDE_ID), GUIDE_SEEN);
	}

	private async pickClosingPeriod(branchId: string): Promise<void> {
		try {
			this.filters.set('rentang', await this.branchPeriod(branchId));
		} catch {
			// Filter tetap seperti sebelumnya; pengguna masih bisa memilih periode lewat Filter.
		}
	}

	openOpening(): void {
		this.actionError = '';
		this.ingredients = [];
		this.openingOpen = true;
	}

	/** The ingredients of the branch chosen in the opening dialog. */
	async loadIngredients(outletId: string): Promise<void> {
		this.ingredients = [];
		if (!outletId) return;
		try {
			this.ingredients = await collectPages((page, size) => api.ingredients.list({ page, size, outlet_id: outletId }));
		} catch (error) {
			this.actionError = userMessage(error, controlText.ingredientsLoadFailed);
		}
	}

	async createOpening(rows: Record<string, string | number>[], outletId: string) {
		const items = rows.map((row) => ({ ingredient_id: String(row.ingredient_id), opening: String(row.opening), from_date: String(row.from_date) }));
		const result = await api.ingredientCounts.opening.createIn(outletId, items);
		await this.load();
		return result;
	}

	/** Membuka lembar bagian yang belum ditutup; bagian stok awal membuka periode yang harus ditutup karena ikut di sana. */
	openRunning(period: CountHistoryRow): Promise<void> {
		const target = period.state === 'opening' ? (this.historyRows.find((row) => row.outlet_id === period.outlet_id && row.state === 'to_close') ?? period) : period;
		this.counted = {};
		this.dirty.clear();
		this.draftBranch = '';
		this.draftSavedAt = '';
		this.sheetBranch = target.outlet_id;
		this.filters.set('cabang', target.outlet_id);
		this.filters.set('rentang', { from: target.start, to: target.end ?? todayIso() });
		return this.load(true);
	}

	closeDialogs(): void {
		this.closing = false;
		this.requesting = false;
		this.openingOpen = false;
		this.actionError = '';
	}
}
