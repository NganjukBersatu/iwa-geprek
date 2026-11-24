import { userMessage } from '$lib/api/user-message';
import { api } from '$lib/api';
import type { StockCandidate, StockItem } from '$lib/api/types';
import { toast } from '$lib/components/feedback/toast.svelte';
import { Filters } from '$lib/components/filter/filters.svelte';
import { ListSort, sortKeys } from '$lib/components/table/list-sort.svelte';
import { STOCK_TABLES } from '$lib/live/tables';
import { ManageState } from '../manage/manage.svelte';
import { branchList } from '$lib/stores/branch';
import { stockColumns } from './columns';
import { BRANCH_SORT } from '$lib/components/table/branch-column';
import { termText } from '$lib/text/terms';
import { stockItemText } from '$lib/text/stock-items';
import { format } from '$lib/text/format';

export type StockRow = StockItem;
export type MovementMode = 'receive' | 'adjust';

const PROBLEMS = 'bermasalah';

/** Stock is kept per branch: the list shows one branch, or every branch (never summed) while none is picked. */
export class StockItemsState extends ManageState<StockRow> {
	override readonly tables = STOCK_TABLES;

	readonly filters = new Filters([
		{ kind: 'select', key: 'cabang', label: termText.branch, options: [] },
		{ kind: 'select', key: 'status_stok', label: termText.status, options: [{ value: PROBLEMS, label: stockItemText.outOrLow }] }
	]);

	readonly sort = new ListSort('barang-stok', [...sortKeys(stockColumns), BRANCH_SORT], () => void this.load());

	outlets = $state<{ id: string; name: string }[]>([]);
	/** The branch of the picker, which has no row to take it from. */
	actionBranch = $state('');
	picking = $state(false);
	candidates = $state<StockCandidate[]>([]);

	get query(): { branch: string | null; problems: boolean } {
		return { branch: this.filters.get('cabang'), problems: this.filters.get('status_stok') === PROBLEMS };
	}

	protected async fetch(): Promise<void> {
		const query = this.query;
		this.outlets = await branchList();
		this.filters.setOptions('cabang', this.outlets.map((outlet) => ({ value: outlet.id, label: outlet.name })));
		const page = await api.stockItems.list(query.problems, this.sort.param);
		this.items = page.items;
		this.total = page.total;
	}

	protected label(item: StockRow): string {
		return item.menu_item_name;
	}

	closeDialogs(): void {
		this.picking = false;
		this.actionError = '';
	}

	openPicker(): void {
		this.actionError = '';
		this.candidates = [];
		this.actionBranch = '';
		this.picking = true;
	}

	/** The menus not yet managed at the branch chosen in the picker. */
	async loadCandidates(): Promise<void> {
		if (!this.actionBranch) return;
		try {
			this.candidates = await api.stockItems.candidates(this.actionBranch);
		} catch (error) {
			this.actionError = userMessage(error, stockItemText.menusLoadFailed);
		}
	}

	async mark(candidate: StockCandidate): Promise<void> {
		const done = await this.attempt(() => api.stockItems.settings(this.actionBranch, candidate.menu_item_id, {}), stockItemText.markFailed);
		if (!done) return;
		this.candidates = this.candidates.filter((item) => item.menu_item_id !== candidate.menu_item_id);
		toast.show(format(stockItemText.nowTracked, { name: candidate.menu_item_name }));
		await this.load();
	}
}
