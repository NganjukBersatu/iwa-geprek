<script lang="ts">
	import { controlText } from '$lib/text/controls';
	import type { AttendanceRecap } from '$lib/api/types';
	import Banner from '$lib/components/card/Banner.svelte';
	import Card from '$lib/components/card/Card.svelte';
	import CardHeader from '$lib/components/card/CardHeader.svelte';
	import Notice from '$lib/components/card/Notice.svelte';
	import SummaryCard from '$lib/components/card/SummaryCard.svelte';
	import DataTable from '$lib/components/table/DataTable.svelte';
	import { EMPTY_VALUE, formatNumber, formatRupiah } from '$lib/format/currency';
	import { formatDuration } from '$lib/format/datetime';
	import type { AttendanceState } from '../attendance.svelte';
	import { userName } from '../names';
	import { attendanceColumns } from '../columns';
	import AttendanceDetail from './AttendanceDetail.svelte';
	import { termText } from '$lib/text/terms';
	import { attendanceReportText } from '$lib/text/attendance-report';
	import { format } from '$lib/text/format';

	let { data, attendance }: { data: AttendanceRecap; attendance: AttendanceState } = $props();

	const count = (value: number) => formatNumber(value, 0);

	const columns = attendanceColumns;
</script>

<div class="grid grid-cols-1 gap-4 tablet:grid-cols-2 laptop:grid-cols-5">
	<SummaryCard
		label={attendanceReportText.totalDeduction}
		caption={format(attendanceReportText.deductionRule, { amount: formatRupiah(data.rule.late_penalty_per_minute), minutes: data.rule.late_tolerance_minutes })}
		value={formatRupiah(data.total_penalty)}
		icon="receipt-2"
		accent="red"
	/>
	<SummaryCard label={attendanceReportText.totalLate} caption={format(attendanceReportText.overtimeTotal, { duration: formatDuration(data.total_overtime_minutes) })} value={format(controlText.minutesCount, { count: count(data.total_late_minutes) })} icon="clock-exclamation" accent="accent" />
	<SummaryCard label={attendanceReportText.sessionsAttended} caption={attendanceReportText.presentPlusLate} value={count(data.total_attended)} icon="user-check" accent="green" />
	<SummaryCard label={termText.absent} caption={attendanceReportText.includesMissing} value={count(data.total_absent)} icon="user-x" accent="red" />
	<SummaryCard
		label={attendanceReportText.revenuePerWorkHour}
		class="tablet:col-span-2 laptop:col-span-1"
		caption={data.revenue_per_work_hour === null
			? attendanceReportText.noWorkHours
			: format(attendanceReportText.revenueOverWork, { revenue: formatRupiah(data.total_revenue), duration: formatDuration(data.total_work_minutes) })}
		value={data.revenue_per_work_hour === null ? EMPTY_VALUE : formatRupiah(data.revenue_per_work_hour)}
		icon="briefcase"
		accent="primary"
	/>
</div>

<Card flush>
	<CardHeader divided title={attendanceReportText.perEmployee} description={format(attendanceReportText.peopleSubtitle, { count: data.user.length, period: attendance.periodLabel })} />
	{#if data.user.length === 0}
		<Notice text={attendanceReportText.noScheduleOrRecords} />
	{:else}
		<DataTable sort={attendance.sort} {columns} rows={data.user} rowKey={(row) => row.user_id} trailing="potongan">
			{#snippet first(row)}
				<span class="block font-semibold text-slate-800">{userName(row)}</span>
				{#if row.name?.trim()}<span class="block text-xs font-normal text-slate-500">@{row.username}</span>{/if}
			{/snippet}
			{#snippet detail(row)}
				<AttendanceDetail user={row} {attendance} />
			{/snippet}
		</DataTable>
	{/if}
</Card>

<Banner tone="accent" icon="info-circle">
	{format(attendanceReportText.lateRuleNote, { minutes: data.rule.late_tolerance_minutes, rate: data.rule.late_tolerance_minutes, example: formatRupiah(data.rule.late_penalty_per_minute) })}
</Banner>
