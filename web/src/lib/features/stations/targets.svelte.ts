import { api } from '$lib/api';
import type { MenuTargetRow } from '$lib/api/types';
import { Filters } from '$lib/components/filter/filters.svelte';
import { pageSize } from '$lib/components/pager/size.svelte';
import { reportPresets } from '$lib/features/report/filters';
import { STATION_TABLES } from '$lib/live/tables';
import { branchList } from '$lib/stores/branch';
import { ManageState } from '../manage/manage.svelte';
import { termText } from '$lib/text/terms';

export type TargetRow = MenuTargetRow & { id: string };

export class TargetsState extends ManageState<TargetRow> {
	override readonly tables = [...STATION_TABLES, 'menu_targets', 'menu_branch_targets', 'menu_items'];

	readonly filters = new Filters([
		{ kind: 'select', key: 'cabang', label: termText.branch, options: [] },
		{ kind: 'date', key: 'rentang', label: termText.range, presets: reportPresets, reach: 'past' }
	]);

	get query(): { search: string | null; branch: string | null; range: { from: string; to: string } | null } {
		return { search: this.search || null, branch: this.filters.get('cabang'), range: this.filters.range('rentang') };
	}

	protected async fetch(): Promise<void> {
		const query = this.query;
		const outlets = await branchList();
		this.filters.setOptions('cabang', outlets.map((outlet) => ({ value: outlet.id, label: outlet.name })));
		const page = await api.stations.targets({
			search: query.search ?? undefined,
			outlet_id: query.branch,
			start: query.range?.from,
			end: query.range?.to,
			page: this.page,
			size: pageSize.value
		});
		this.items = page.items.map((row) => ({ ...row, id: row.menu_id }));
		this.total = page.total;
	}

	protected label(row: TargetRow): string {
		return row.name;
	}
}
