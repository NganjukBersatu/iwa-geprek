import { ApiError } from '$lib/api/http';
import { userMessage } from '$lib/api/user-message';
import { browser } from '$app/environment';
import { api } from '$lib/api';
import type { Deposit, DepositCreate, DepositDay, DepositDays } from '$lib/api/types';
import { access } from '$lib/auth/access.svelte';
import { toast } from '$lib/components/feedback/toast.svelte';
import type { Filters } from '$lib/components/filter/filters.svelte';
import { ListSort, sortKeys } from '$lib/components/table/list-sort.svelte';
import { Selection } from '$lib/components/table/selection.svelte';
import type { DateRange } from '$lib/date/range';
import { dayColumns, shareColumns } from './columns';
import { depositText } from '$lib/text/deposits';
import { format } from '$lib/text/format';

const COLUMNS_KEY = 'overview.setoran.kolom';
export const HELD = 'dipegang';
export const SETTLED = 'lunas';

export type DepositTab = 'overview' | 'riwayat';
export type DepositForm = { days: string[] };
export type DepositDetail = { kind: 'day' | 'deposit'; id: string };

function readColumns(): boolean {
	if (!browser) return false;
	try {
		return localStorage.getItem(COLUMNS_KEY) === '1';
	} catch {
		return false;
	}
}

/** Cash handed over to the owner for one branch: what each day still holds, the deposits that settled it, and the dialogs around them. */
export class DepositsState {
	get canView(): boolean {
		return access.allows('view_deposits');
	}

	get canManage(): boolean {
		return access.allows('manage_deposits');
	}
	/** The days picked for one deposit; the checkboxes only show once the person switches to picking several. */
	readonly selection = new Selection();
	readonly daySort = new ListSort('setoran-hari', sortKeys(dayColumns), () => void this.load(this.range, true));
	readonly shareSort = new ListSort('setoran-alokasi', sortKeys(shareColumns(() => undefined)), () => void this.load(this.range, true));

	data = $state<DepositDays | null>(null);
	deposits = $state<Deposit[]>([]);
	loading = $state(false);
	error = $state('');
	busy = $state(false);
	actionError = $state('');
	/** What the server refused about the form, by field name, shown under each field. */
	fieldErrors = $state<Record<string, string>>({});
	tab = $state<DepositTab>('overview');
	/** The Setoran columns of the table stay hidden until asked for. */
	columns = $state(readColumns());
	form = $state<DepositForm | null>(null);
	/** The days of the branch the open form writes to; the table above may add several branches together. */
	formDays = $state<DepositDay[]>([]);
	detail = $state<DepositDetail | null>(null);
	removing = $state<Deposit | null>(null);

	private range: DateRange | null = null;
	private token = 0;

	constructor(private filters: Filters) {}

	get filter(): string | null {
		return this.filters.get('setoran');
	}

	/** Whether the figures add up every branch: no branch is picked. */
	get allBranches(): boolean {
		return this.filters.allBranches;
	}

	readonly byDay = $derived(new Map((this.data?.items ?? []).map((item) => [item.day, item])));
	readonly openDays = $derived((this.data?.items ?? []).filter((item) => Number(item.left) > 0).map((item) => item.day));

	dayOf(date: string): DepositDay | undefined {
		return this.byDay.get(date);
	}

	/** Whether a date stays in the table under the Setoran filter; dates that owe nothing only show without a filter. */
	keeps(date: string): boolean {
		const filter = this.filter;
		if (!filter) return true;
		const day = this.byDay.get(date);
		if (!day) return false;
		return filter === HELD ? Number(day.left) > 0 : Number(day.left) <= 0;
	}

	get detailDay(): DepositDay | null {
		return this.detail?.kind === 'day' ? (this.byDay.get(this.detail.id) ?? null) : null;
	}

	get detailDeposit(): Deposit | null {
		return this.detail?.kind === 'deposit' ? (this.deposits.find((deposit) => deposit.id === this.detail?.id) ?? null) : null;
	}

	depositsOfDay(date: string): Deposit[] {
		return this.deposits.filter((deposit) => deposit.days.some((share) => share.day === date));
	}

	setColumns(on: boolean): void {
		this.columns = on;
		if (!browser) return;
		try {
			localStorage.setItem(COLUMNS_KEY, on ? '1' : '0');
		} catch {
			// Remembering the choice is only a convenience.
		}
	}

	clear(): void {
		this.token++;
		this.range = null;
		this.data = null;
		this.deposits = [];
		this.loading = false;
		this.error = '';
		this.selection.stop();
	}

	async load(range: DateRange | null = this.range, quiet = false): Promise<void> {
		if (!range || !this.canView) return;
		this.range = range;
		const token = ++this.token;
		if (!quiet) this.loading = true;
		if (!quiet) this.error = '';
		try {
			const params = { start: range.from, end: range.to };
			const [data, deposits] = await Promise.all([api.deposits.days({ ...params, sort: this.daySort.param }), api.deposits.list({ ...params, share_sort: this.shareSort.param })]);
			if (token !== this.token) return;
			this.data = data;
			this.deposits = deposits;
		} catch (error) {
			if (token !== this.token || quiet) return;
			this.data = null;
			this.deposits = [];
			this.error = userMessage(error, depositText.loadFailed);
		} finally {
			if (token === this.token) this.loading = false;
		}
	}

	private async attempt(work: () => Promise<void>, fallback: string): Promise<boolean> {
		this.busy = true;
		this.actionError = '';
		this.fieldErrors = {};
		try {
			await work();
			return true;
		} catch (error) {
			this.fieldErrors = error instanceof ApiError ? error.fieldErrors : {};
			this.actionError = userMessage(error, fallback);
			return false;
		} finally {
			this.busy = false;
		}
	}

	/** With days ticked the deposit settles those; with none it settles every day still held, oldest first. */
	openCreate(days?: string[]): void {
		const chosen = days ?? (this.selection.count > 0 ? this.selection.ids : this.openDays);
		if (chosen.length === 0) {
			toast.show(depositText.allDeposited);
			return;
		}
		this.actionError = '';
		this.detail = null;
		this.formDays = [];
		this.form = { days: [...chosen].sort() };
	}

	/** Reads the days of the branch chosen in the form, so the amount offered is that branch's own. */
	async loadFormDays(outletId: string): Promise<void> {
		this.formDays = [];
		if (!outletId || !this.range) return;
		try {
			this.formDays = (await api.deposits.daysOf(outletId, { start: this.range.from, end: this.range.to })).items;
		} catch (error) {
			this.actionError = userMessage(error, depositText.daysLoadFailed);
		}
	}

	/** What is still held on these days at the branch chosen in the form. */
	formLeft(days: string[]): number {
		return days.reduce((sum, day) => sum + Number(this.formDays.find((item) => item.day === day)?.left ?? 0), 0);
	}

	closeDialogs(): void {
		this.form = null;
		this.detail = null;
		this.removing = null;
		this.actionError = '';
	}

	async save(body: DepositCreate, photo: File | null, outletId: string): Promise<void> {
		let created: Deposit | null = null;
		const done = await this.attempt(async () => {
			created = await api.deposits.create(outletId, body);
		}, depositText.recordFailed);
		if (!done || !created) return;
		this.form = null;
		this.selection.stop();
		let photoError = '';
		if (photo) {
			try {
				await api.deposits.uploadPhoto(created as Deposit, photo);
			} catch (error) {
				photoError = userMessage(error, depositText.receiptUploadFailed);
			}
		}
		if (photoError) toast.show(format(depositText.depositRecordedPhotoFailed, { detail: photoError }), 'error');
		else toast.show(photo ? depositText.recordedWithReceipt : depositText.recorded);
		await this.load(this.range, true);
	}

	async replacePhoto(deposit: Deposit, file: File): Promise<void> {
		const done = await this.attempt(async () => {
			await api.deposits.uploadPhoto(deposit, file);
		}, depositText.receiptSaveFailed);
		if (!done) return;
		toast.show(depositText.receiptSaved);
		await this.load(this.range, true);
	}

	askCancel(deposit: Deposit): void {
		this.actionError = '';
		this.removing = deposit;
	}

	async confirmCancel(): Promise<void> {
		const target = this.removing;
		if (!target) return;
		const done = await this.attempt(() => api.deposits.cancel(target), depositText.cancelFailed);
		if (!done) return;
		this.removing = null;
		this.detail = null;
		toast.show(depositText.cancelled);
		await this.load(this.range, true);
	}
}
