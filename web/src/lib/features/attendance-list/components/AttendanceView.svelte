<script lang="ts">
	import { dynamicStyle } from '$lib/motion/actions';
	import { goto } from '$app/navigation';
	import { attendancePath } from '$lib/nav/pages';
	import Badge from '$lib/components/card/Badge.svelte';
	import Card from '$lib/components/card/Card.svelte';
	import CardHeader from '$lib/components/card/CardHeader.svelte';
	import ListSearch from '$lib/components/filter/ListSearch.svelte';
	import { noMatchText } from '$lib/components/filter/no-match';
	import Notice from '$lib/components/card/Notice.svelte';
	import Pager from '$lib/components/pager/Pager.svelte';
	import DataTable from '$lib/components/table/DataTable.svelte';
	import { EMPTY_VALUE, formatNumber } from '$lib/format/currency';
	import type { AttendanceListState } from '../attendance-list.svelte';
	import { attendanceColumns } from '../columns';
	import { STATUS_TONES } from '../labels';
	import { attendanceListText } from '$lib/text/attendance-list';
	import { format } from '$lib/text/format';

	let { attendance }: { attendance: AttendanceListState } = $props();

	const columns = attendanceColumns;

</script>

<Card flush>
	<CardHeader divided title={attendanceListText.listTitle} description={format(attendanceListText.listDescriptionWithCount, { count: formatNumber(attendance.total, 0) })} />
	<ListSearch value={attendance.search} placeholder={attendanceListText.searchPlaceholder} label={attendanceListText.search} onsearch={(query) => attendance.setSearch(query)} />
	{#if attendance.items.length === 0}
		<Notice text={noMatchText('catatan', attendance.search !== '', attendance.filters.count > 0) ?? attendanceListText.noRecords} />
	{:else}
		<DataTable sort={attendance.sort} {columns} rows={attendance.items} rowKey={(row) => row.id} loading={attendance.loading} trailing="status" onopen={(row) => void goto(attendancePath(row.id))}>
			{#snippet first(row)}
				<span class="block">{row.name || row.username}</span>
				<span class="block text-xs font-normal text-slate-500">@{row.username}{row.role_name ? ` · ${row.role_name}` : ''}</span>
			{/snippet}
			{#snippet cell(row, column)}
				{#if column.key === 'status'}
					<span class="inline-flex flex-wrap items-center gap-1">
						<Badge tone={STATUS_TONES[row.status]}>{column.value(row)}</Badge>
						{#if row.auto_closed}<Badge tone="neutral" title={attendanceListText.autoClosedHint}>{attendanceListText.autoClosed}</Badge>{/if}
					</span>
				{:else if column.key === 'kode'}
					{#if row.shift_code}
						<span class="inline-flex items-center gap-1.5"><span class="size-2.5 rounded-full bg-slate-300" use:dynamicStyle={{ 'background-color': row.shift_code_color }}></span>{row.shift_code}</span>
					{:else}
						{EMPTY_VALUE}
					{/if}
				{:else}
					{column.value(row)}
				{/if}
			{/snippet}
		</DataTable>
		<div class="border-t border-slate-100 px-4 pb-4 tablet:px-5">
			<Pager page={attendance.page} total={attendance.total} unit="catatan" disabled={attendance.loading} onchange={(page) => attendance.setPage(page)} />
		</div>
	{/if}
</Card>
