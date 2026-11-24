import { userMessage } from '$lib/api/user-message';
import { rupiahDigits } from '$lib/format/currency';
import { api } from '$lib/api';
import type { CheckStatus, NonCashCheckRow, NonCashChecks } from '$lib/api/types';
import type { Filters } from '$lib/components/filter/filters.svelte';
import { BRANCH_SORT } from '$lib/components/table/branch-column';
import { ListSort, sortKeys } from '$lib/components/table/list-sort.svelte';
import type { DateRange } from '$lib/date/range';
import { qcColumns } from './columns';
import { financeText } from '$lib/text/finance';

export const rowKey = (row: NonCashCheckRow): string => `${row.date}:${row.outlet_id}`;

export class QcState {
	report = $state<NonCashChecks | null>(null);
	readonly sort = new ListSort('qc-non-tunai', [...sortKeys(qcColumns(false, '')), BRANCH_SORT], () => void this.load(this.range, true));
	loading = $state(false);
	error = $state('');
	/** The row being saved: a day of one branch. */
	savingKey = $state<string | null>(null);

	private range: DateRange | null = null;
	private token = 0;
	private loadedStatus = '';

	constructor(private filters: Filters) {}

	get status(): CheckStatus | 'all' {
		return (this.filters.get('status_qc') as CheckStatus | null) ?? 'all';
	}

	clear(): void {
		this.token++;
		this.range = null;
		this.report = null;
		this.loading = false;
		this.error = '';
	}

	reloadIfChanged(): void {
		if (this.status !== this.loadedStatus) void this.load();
	}

	async load(range: DateRange | null = this.range, quiet = false): Promise<void> {
		if (!range) return;
		this.range = range;
		this.loadedStatus = this.status;
		const token = ++this.token;
		if (!quiet) this.loading = true;
		if (!quiet) this.error = '';
		try {
			const report = await api.qc.list({ start: range.from, end: range.to, status: this.status, sort: this.sort.param });
			if (token === this.token) this.report = report;
		} catch (error) {
			if (token !== this.token || quiet) return;
			this.report = null;
			this.error = userMessage(error, financeText.qcLoadFailed);
		} finally {
			if (token === this.token) this.loading = false;
		}
	}

	async save(row: NonCashCheckRow, raw: string): Promise<void> {
		const amount = rupiahDigits(raw);
		const previous = row.bank_amount;
		if (amount === '' && previous === null) return;
		if (amount !== '' && previous !== null && Number(amount) === Math.round(Number(previous))) return;
		this.savingKey = rowKey(row);
		this.error = '';
		try {
			if (amount === '') await api.qc.remove(row);
			else await api.qc.save(row, Number(amount));
			await this.load();
		} catch (error) {
			this.error = userMessage(error, financeText.saveFailed);
		} finally {
			this.savingKey = null;
		}
	}
}
