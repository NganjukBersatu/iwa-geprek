import { api } from '$lib/api';
import { Filters } from '$lib/components/filter/filters.svelte';
import { pageOf } from '$lib/components/pager/page-of';
import { branchPeriodText } from '$lib/text/branch-periods';
import { branchList } from '$lib/stores/branch';
import { ManageState } from '../manage/manage.svelte';
import type { PeriodRow } from './columns';
import { periodLabel } from './period-label';

export class BranchPeriodsState extends ManageState<PeriodRow> {
	override readonly tables = ['branch_periods', 'outlets'];

	readonly filters = new Filters([{ kind: 'select', key: 'cabang', label: branchPeriodText.branchFilter, options: [] }]);

	get query(): { branch: string | null } {
		return { branch: this.filters.get('cabang') };
	}

	/** Paling banyak dua belas periode per cabang, jadi semuanya dimuat sekali lalu dibagi per halaman di layar. */
	get visible(): { rows: PeriodRow[]; page: number } {
		return pageOf(this.items, this.page);
	}

	protected async fetch(): Promise<void> {
		const outlets = await branchList();
		this.filters.setOptions('cabang', outlets.map((outlet) => ({ value: outlet.id, label: outlet.name })));
		const periods = await api.outlets.periods(this.query.branch ?? undefined);
		this.items = periods.map((period) => ({ ...period, id: `${period.outlet_id}:${period.start}` }));
		this.total = this.items.length;
	}

	protected label(row: PeriodRow): string {
		return `${row.outlet_name} ${periodLabel(row)}`;
	}
}
