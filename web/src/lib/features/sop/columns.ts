import type { SopSummary } from '$lib/api/types';
import type { Column } from '$lib/components/table/types';
import { EMPTY_VALUE } from '$lib/format/currency';
import { formatDateTime } from '$lib/format/datetime';
import { termText } from '$lib/text/terms';
import { sopText } from '$lib/text/sop';
import { format } from '$lib/text/format';

const EVERY_BRANCH = termText.allBranches;

export const branchOf = (row: SopSummary) => row.outlet_name ?? (row.outlet_id ? EMPTY_VALUE : EVERY_BRANCH);
const changed = (row: SopSummary) => `${formatDateTime(row.updated_at)}${row.updated_by ? ` · ${row.updated_by}` : ''}`;

export const sopColumns: Column<SopSummary>[] = [
	{ key: 'judul', label: 'SOP', align: 'left', value: (row) => row.title, sort: 'title' },
	{ key: 'cabang', label: sopText.availableIn, align: 'left', value: branchOf, sort: 'branch' },
	{ key: 'slide', label: sopText.slide, value: (row) => format(sopText.slidesCount, { count: row.slide_count }), sort: 'slides' },
	{ key: 'versi', label: sopText.version, value: (row) => `versi ${row.version}`, sort: 'version' },
	{ key: 'status', label: termText.status, align: 'left', value: (row) => (row.active ? sopText.shown : sopText.hidden), sort: 'status' },
	{ key: 'diubah', label: sopText.changed, align: 'left', value: changed, sort: 'updated_at' }
];
