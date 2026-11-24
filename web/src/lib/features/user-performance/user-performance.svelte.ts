import { api } from '$lib/api';
import type { PerformanceListRange, UserPerformanceQuery } from '$lib/api/userPerformance';
import type { UserPerformanceRow } from '$lib/api/types';
import { Filters } from '$lib/components/filter/filters.svelte';
import { pageSize } from '$lib/components/pager/size.svelte';
import { ListSort, sortKeys } from '$lib/components/table/list-sort.svelte';
import { PERFORMANCE_TABLES } from '$lib/live/tables';
import { branchList } from '$lib/stores/branch';
import { collectPages } from '../manage/collect';
import { userPerformanceText as t } from '$lib/text/user-performance';
import { ManageState } from '../manage/manage.svelte';
import { performanceColumns, type PerformanceRow } from './columns';

export type PerformanceListQuery = { range: PerformanceListRange; search: string | null; branch: string | null };

/** The performance of every active employee in their own pay cycle, computed by the server with the same formula as the employee app. */
export class UserPerformanceState extends ManageState<PerformanceRow> {
	override readonly tables = PERFORMANCE_TABLES;
	readonly sort = new ListSort('user-performance', sortKeys(performanceColumns), () => void this.queryChanged());
	readonly filters = new Filters([{ kind: 'select', key: 'cabang', label: t.columns.branch, options: [] }]);

	range = $state<PerformanceListRange>('cycle');

	get query(): PerformanceListQuery {
		return { range: this.range, search: this.search || null, branch: this.filters.get('cabang') };
	}

	private params(page: number, size: number): UserPerformanceQuery {
		const query = this.query;
		return { range: query.range, search: query.search ?? undefined, outlet_id: query.branch ?? undefined, sort: this.sort.param, page, size };
	}

	private static rows(items: UserPerformanceRow[]): PerformanceRow[] {
		return items.map((item) => ({ ...item, id: item.user_id }));
	}

	protected override async allRows(): Promise<PerformanceRow[]> {
		return UserPerformanceState.rows(await collectPages((page, size) => api.userPerformance.list(this.params(page, size))));
	}

	protected async fetch(): Promise<void> {
		const [result, outlets] = await Promise.all([api.userPerformance.list(this.params(this.page, pageSize.value)), branchList()]);
		this.items = UserPerformanceState.rows(result.items);
		this.total = result.total;
		this.filters.setOptions('cabang', outlets.map((outlet) => ({ value: outlet.id, label: outlet.name })));
	}

	protected label(row: PerformanceRow): string {
		return row.name;
	}
}
