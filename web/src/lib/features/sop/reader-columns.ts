import type { SopReader } from '$lib/api/types';
import type { Column } from '$lib/components/table/types';
import { EMPTY_VALUE } from '$lib/format/currency';
import { formatDateTime } from '$lib/format/datetime';
import { format } from '$lib/text/format';
import { sopReadersText } from '$lib/text/sop-readers';

/** One row of a reader; the id is the employee account, since one person appears once per SOP. */
export type ReaderRow = SopReader & { id: string };

export const readerStatus = (row: ReaderRow): string =>
	row.current ? sopReadersText.statusRead : row.read_version === null ? sopReadersText.statusUnread : format(sopReadersText.statusOldVersion, { version: row.read_version });

export const readerColumns: Column<ReaderRow>[] = [
	{ key: 'name', label: sopReadersText.columnEmployee, align: 'left', value: (row) => row.name, sort: 'name' },
	{ key: 'role', label: sopReadersText.columnRole, align: 'left', value: (row) => row.role_name ?? EMPTY_VALUE, sort: 'role' },
	{ key: 'branch', label: sopReadersText.columnBranch, align: 'left', value: (row) => row.outlet_name ?? sopReadersText.allBranches, sort: 'outlet' },
	{ key: 'status', label: sopReadersText.columnStatus, align: 'left', value: readerStatus },
	{ key: 'readAt', label: sopReadersText.columnReadAt, align: 'left', value: (row) => (row.read_at ? formatDateTime(row.read_at) : EMPTY_VALUE), sort: 'read_at' }
];
