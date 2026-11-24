import { api } from '$lib/api';
import type { SopReaderQuery } from '$lib/api/sop';
import type { SopReader } from '$lib/api/types';
import { Filters } from '$lib/components/filter/filters.svelte';
import { pageSize } from '$lib/components/pager/size.svelte';
import { ListSort, sortKeys } from '$lib/components/table/list-sort.svelte';
import { branchList } from '$lib/stores/branch';
import { sopReadersText } from '$lib/text/sop-readers';
import { collectPages } from '../manage/collect';
import { ManageState } from '../manage/manage.svelte';
import { readerColumns, type ReaderRow } from './reader-columns';

export type ReaderFilterQuery = { status: string | null; branch: string | null };

const STATUS_READ = 'read';
const STATUS_UNREAD = 'unread';

/** Who has and has not read one SOP to its last slide; reloaded each time an employee finishes reading. */
export class SopReadersState extends ManageState<ReaderRow> {
	override readonly tables = ['sop_reads', 'sop', 'users'];
	readonly sort = new ListSort('sop-readers', sortKeys(readerColumns), () => void this.queryChanged());

	readonly filters = new Filters([
		{
			kind: 'select',
			key: 'sop-read-status',
			label: sopReadersText.filterStatus,
			options: [
				{ value: STATUS_READ, label: sopReadersText.filterRead },
				{ value: STATUS_UNREAD, label: sopReadersText.filterUnread }
			]
		},
		{ kind: 'select', key: 'cabang', label: sopReadersText.filterBranch, options: [] }
	]);

	title = $state('');
	version = $state(0);
	readCount = $state(0);
	audienceCount = $state(0);

	constructor(readonly sopId: string) {
		super();
	}

	get query(): ReaderFilterQuery {
		return { status: this.filters.get('sop-read-status'), branch: this.filters.get('cabang') };
	}

	private params(page: number, size: number): SopReaderQuery {
		const status = this.query.status;
		return {
			outlet_id: this.query.branch ?? undefined,
			read: status === null ? undefined : status === STATUS_READ,
			sort: this.sort.param,
			page,
			size
		};
	}

	private static rows(items: SopReader[]): ReaderRow[] {
		return items.map((item) => ({ ...item, id: item.user_id }));
	}

	protected override async allRows(): Promise<ReaderRow[]> {
		return SopReadersState.rows(await collectPages((page, size) => api.sop.readers(this.sopId, this.params(page, size))));
	}

	protected async fetch(): Promise<void> {
		const [result, outlets] = await Promise.all([api.sop.readers(this.sopId, this.params(this.page, pageSize.value)), branchList()]);
		this.items = SopReadersState.rows(result.items);
		this.total = result.total;
		this.title = result.title;
		this.version = result.version;
		this.readCount = result.read_count;
		this.audienceCount = result.audience_count;
		this.filters.setOptions('cabang', outlets.map((outlet) => ({ value: outlet.id, label: outlet.name })));
	}

	protected label(row: ReaderRow): string {
		return row.name;
	}
}
