import { api } from '$lib/api';
import type { SessionHistoryPage } from '$lib/api/types';
import { pageSize } from '$lib/components/pager/size.svelte';
import type { DateRange } from '$lib/date/range';
import { createReportFilters } from '../report/filters';
import { SESSION_TABLES } from '$lib/live/tables';
import { rangeParams, ReportState } from '../report/report.svelte';
import { ListSort, sortKeys } from '$lib/components/table/list-sort.svelte';
import { sessionHistoryColumns } from './columns';
import { termText } from '$lib/text/terms';

const RUNNING = 'berjalan';
const CLOSED = 'ditutup';

type HistoryQuery = { branch: string | null; range: DateRange | null; status: string | null; search: string | null };

export class SessionHistoryState extends ReportState<HistoryQuery, SessionHistoryPage> {
	override readonly tables = SESSION_TABLES;
	readonly sort = new ListSort('riwayat-sesi', sortKeys(sessionHistoryColumns), () => void this.queryChanged(this.query));

	filters = createReportFilters([
		{
			kind: 'select',
			key: 'status_sesi',
			label: termText.status,
			options: [
				{ value: RUNNING, label: termText.running },
				{ value: CLOSED, label: termText.closed }
			]
		}
	]);

	get query(): HistoryQuery {
		return { branch: this.filters.get('cabang'), range: this.filters.range('rentang'), status: this.filters.get('status_sesi'), search: this.search || null };
	}

	protected fetch(query: HistoryQuery): Promise<SessionHistoryPage> {
		return api.sessions.history({
			...rangeParams(query.range),
			running: query.status === RUNNING ? true : query.status === CLOSED ? false : undefined,
			search: query.search ?? undefined,
			sort: this.sort.param,
			page: this.page,
			size: pageSize.value
		});
	}
}
