import { api } from '$lib/api';
import type { Expense } from '$lib/api/types';
import { toast } from '$lib/components/feedback/toast.svelte';
import { EXPENSE_TABLES } from '$lib/live/tables';
import { Filters } from '$lib/components/filter/filters.svelte';
import { pageSize } from '$lib/components/pager/size.svelte';
import type { DateRange } from '$lib/date/range';
import { FUND_SOURCES } from '../finance/fund-sources';
import { collectPages } from '../manage/collect';
import { DayWarning } from '../deposits/day-warning.svelte';
import { ListSort, sortKeys } from '$lib/components/table/list-sort.svelte';
import { expenseColumns } from './columns';
import { ManageState } from '../manage/manage.svelte';
import { reportPresets } from '../report/filters';
import { branchList } from '$lib/stores/branch';
import { termText } from '$lib/text/terms';
import { expenseText } from '$lib/text/expenses';

export type ExpenseQuery = { search: string | null; branch: string | null; range: DateRange | null; source: string | null };

export class ExpensesState extends ManageState<Expense> {
	override readonly tables = EXPENSE_TABLES;
	readonly sort = new ListSort('pengeluaran', sortKeys(expenseColumns), () => void this.queryChanged());

	readonly filters = new Filters([
		{ kind: 'select', key: 'cabang', label: termText.branch, options: [] },
		{ kind: 'date', key: 'rentang', label: termText.range, presets: reportPresets, reach: 'past' },
		{ kind: 'select', key: 'sumber', label: expenseText.fundingSource, options: Object.entries(FUND_SOURCES).map(([value, label]) => ({ value, label })) }
	]);

	totalAmount = $state('0');
	drawerAmount = $state('0');
	readonly warning = new DayWarning();
	bulkRemoveOpen = $state(false);

	get query(): ExpenseQuery {
		return { search: this.search || null, branch: this.filters.get('cabang'), range: this.filters.range('rentang'), source: this.filters.get('sumber') };
	}

	private params(page: number, size: number) {
		const query = this.query;
		return { search: query.search ?? undefined, start: query.range?.from, end: query.range?.to, fund_source: query.source ?? undefined, sort: this.sort.param, page, size };
	}

	protected override allRows(): Promise<Expense[]> {
		return collectPages((page, size) => api.expenses.list(this.params(page, size)));
	}

	protected async fetch(): Promise<void> {
		const query = this.query;
		const [page, outlets] = await Promise.all([
			api.expenses.list(this.params(this.page, pageSize.value)),
			branchList()
		]);
		this.filters.setOptions('cabang', outlets.map((outlet) => ({ value: outlet.id, label: outlet.name })));
		this.items = page.items;
		this.total = page.total;
		this.totalAmount = String(page.total_amount);
		this.drawerAmount = String(page.drawer_amount);
	}

	protected label(expense: Expense): string {
		return expense.item_name;
	}

	/** Called as the bulk delete asks for its confirmation. */
	checkSelected(): void {
		void this.warning.readExpenses(this.selection.ids);
	}

	closeDialogs(): void {
		this.bulkRemoveOpen = false;
		this.actionError = '';
		this.warning.clear();
	}

	async removeSelected(): Promise<void> {
		await this.bulk('dihapus', (ids) => api.expenses.bulk.remove(ids), () => (this.bulkRemoveOpen = false));
	}
}
