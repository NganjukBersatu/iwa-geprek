import type { Batch } from '$lib/api/types';
import type { Column } from '$lib/components/table/types';
import { formatClockRange } from '$lib/format/datetime';
import { batchText } from '$lib/text/batches';
import { format } from '$lib/text/format';
import { fillLabel, recipientLabel, repeatLabel, type BatchKind } from './constants';

const shared: Column<Batch>[] = [
	{ key: 'hours', label: batchText.columnHours, align: 'left', value: (row) => formatClockRange(row.start_clock, row.end_clock), sort: 'hours' },
	{ key: 'repeat', label: batchText.columnRepeat, align: 'left', value: (row) => repeatLabel(row), sort: 'days' },
	{ key: 'items', label: batchText.columnItems, value: (row) => format(batchText.itemsCount, { count: row.items.length }), sort: 'items' },
	{ key: 'status', label: batchText.columnStatus, align: 'left', value: (row) => (row.is_active ? batchText.statusActive : batchText.statusInactive), sort: 'status' }
];

const routine: Column<Batch>[] = [
	{ key: 'recipient', label: batchText.columnRecipient, align: 'left', value: (row) => recipientLabel(row) },
	{ key: 'filler', label: batchText.columnFiller, align: 'left', value: (row) => fillLabel(row.fill_mode) }
];

export function batchColumns(kind: BatchKind): Column<Batch>[] {
	const name: Column<Batch> = { key: 'name', label: batchText.kinds[kind].title, align: 'left', value: (row) => row.name, sort: 'name' };
	return kind === 'routine' ? [name, ...routine, ...shared] : [name, ...shared];
}
