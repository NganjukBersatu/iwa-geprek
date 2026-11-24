import { api } from '$lib/api';
import type { MoneyChangeParams } from '$lib/api/moneyChanges';
import type { MoneyChange, MoneyChangeReport, MoneySubject } from '$lib/api/types';
import { pageSize } from '$lib/components/pager/size.svelte';
import type { DateRange } from '$lib/date/range';
import { SALES_TABLES } from '$lib/live/tables';
import { collectPages } from '../manage/collect';
import { createReportFilters } from '../report/filters';
import { rangeParams, ReportState } from '../report/report.svelte';
import { SUBJECT_LABELS } from './labels';
import { ListSort, sortKeys } from '$lib/components/table/list-sort.svelte';
import { moneyChangeColumns } from './columns';
import { termText } from '$lib/text/terms';

type ChangesQuery = { branch: string | null; range: DateRange | null; subject: MoneySubject | null };

const SUBJECTS = Object.keys(SUBJECT_LABELS) as MoneySubject[];
const isSubject = (value: string | null): value is MoneySubject => value !== null && (SUBJECTS as string[]).includes(value);

const paramsOf = (query: ChangesQuery, page: number, size: number): MoneyChangeParams => ({ ...rangeParams(query.range), subject: query.subject ?? undefined, page, size });

export class MoneyChangesState extends ReportState<ChangesQuery, MoneyChangeReport> {
	override readonly tables = SALES_TABLES;
	readonly sort = new ListSort('jejak-uang', sortKeys(moneyChangeColumns(true)), () => void this.queryChanged(this.query));

	filters = createReportFilters([
		{ kind: 'select', key: 'jenis_uang', label: termText.kind, options: SUBJECTS.map((subject) => ({ value: subject, label: SUBJECT_LABELS[subject] })) }
	]);

	get query(): ChangesQuery {
		const subject = this.filters.get('jenis_uang');
		return { branch: this.filters.get('cabang'), range: this.filters.range('rentang'), subject: isSubject(subject) ? subject : null };
	}

	protected fetch(query: ChangesQuery): Promise<MoneyChangeReport> {
		return api.moneyChanges.list({ ...paramsOf(query, this.page, pageSize.value), sort: this.sort.param });
	}

	get allBranches(): boolean {
		return this.filters.allBranches;
	}

	exportRows(): Promise<MoneyChange[]> {
		const query = this.query;
		return collectPages(async (page, size) => {
			const result = await api.moneyChanges.list({ ...paramsOf(query, page, size), sort: this.sort.param });
			return { items: result.items, total: result.total };
		});
	}
}
