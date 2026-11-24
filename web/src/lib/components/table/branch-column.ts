import type { Column } from './types';
import { termText } from '$lib/text/terms';

/** The sort key every per-branch list offers for its Cabang column. */
export const BRANCH_SORT = 'outlet';

/** The Cabang column every list of per-branch rows shows while it covers all branches, placed right after the lead column. */
export function withBranchColumn<T extends { outlet_name: string }>(columns: Column<T>[], allBranches: boolean, sort?: typeof BRANCH_SORT): Column<T>[] {
	if (!allBranches) return columns;
	const [lead, ...rest] = columns;
	if (!lead) return columns;
	return [lead, { key: 'cabang', label: termText.branch, align: 'left', value: (row) => row.outlet_name, sort }, ...rest];
}
