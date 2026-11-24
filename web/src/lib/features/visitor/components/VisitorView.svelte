<script lang="ts">
	import { QUIET_VALUE } from '$lib/components/table/quiet-value';
	import type { VisitorBreakdown } from '$lib/api/types';
	import Badge from '$lib/components/card/Badge.svelte';
	import Card from '$lib/components/card/Card.svelte';
	import CardHeader from '$lib/components/card/CardHeader.svelte';
	import Notice from '$lib/components/card/Notice.svelte';
	import Banner from '$lib/components/card/Banner.svelte';
	import SummaryCard from '$lib/components/card/SummaryCard.svelte';
	import SeriesChart from '$lib/components/chart/SeriesChart.svelte';
	import DataTable from '$lib/components/table/DataTable.svelte';
	import { chartCategories, chartInk, chartPalette } from '$lib/charts/theme';
	import { dayLabel, formatDayMonth, shiftDays, todayIso } from '$lib/date/range';
	import { formatNumber, formatPercentPlain, formatRupiah } from '$lib/format/currency';
	import { dayColumns, groupColumns, UNRECORDED } from '../columns';
	import type { VisitorState } from '../visitor.svelte';
	import { termText } from '$lib/text/terms';
	import { visitorText } from '$lib/text/visitor';
	import { format } from '$lib/text/format';

	let { data, visitor }: { data: VisitorBreakdown; visitor: VisitorState } = $props();

	const share = (part: number, total: number) => (total > 0 ? formatPercentPlain((part / total) * 100) : '0%');

	const labels = $derived(visitor.dimension === 'gender' ? data.gender_labels : data.category_labels);
	const today = todayIso();
	const marker = (iso: string) => (iso === today ? visitorText.today : iso === shiftDays(today, -1) ? visitorText.yesterday : '');

	const days = $derived(dayColumns(data.gender_labels, data.category_labels));

	const series = $derived(
		visitor.metric === 'omzet'
			? [{ name: termText.revenue, values: data.days.map((day) => Number(day.revenue)), color: chartPalette.income }]
			: labels.map((label, index) => ({
					name: label,
					values: data.days.map((day) => (visitor.dimension === 'gender' ? day.genders : day.categories)[label] ?? 0),
					color: label === UNRECORDED ? chartInk.axis : chartCategories[index % chartCategories.length]!,
					stack: 'harian'
				}))
	);
</script>

{#if data.total_transactions > 0 && (data.with_category < data.total_transactions || data.with_gender < data.total_transactions)}
	<Banner tone="info" icon="info-circle" title={visitorText.unrecordedTitle}>
		{format(visitorText.unrecordedNote, {
			category: formatNumber(data.with_category, 0),
			gender: formatNumber(data.with_gender, 0),
			total: formatNumber(data.total_transactions, 0)
		})}
	</Banner>
{/if}

<div class="grid grid-cols-1 gap-4 tablet:grid-cols-2 laptop:grid-cols-4">
	<SummaryCard label={termText.transaction} caption={visitorText.validTransactions} value={formatNumber(data.total_transactions, 0)} icon="receipt" accent="primary" />
	<SummaryCard label={termText.revenue} caption={visitorText.periodTotal} value={formatRupiah(data.total_revenue)} icon="wallet" accent="accent" />
	<SummaryCard
		label={visitorText.categoryRecorded}
		caption={format(visitorText.ofTransactions, { count: formatNumber(data.with_category, 0), total: formatNumber(data.total_transactions, 0) })}
		value={share(data.with_category, data.total_transactions)}
		icon="category"
		accent="ink"
	/>
	<SummaryCard
		label={visitorText.genderRecorded}
		caption={format(visitorText.ofTransactions, { count: formatNumber(data.with_gender, 0), total: formatNumber(data.total_transactions, 0) })}
		value={share(data.with_gender, data.total_transactions)}
		icon="gender-bigender"
		accent="plain"
	/>
</div>

<div class="grid grid-cols-1 gap-4 laptop:grid-cols-2 tablet:gap-6">
	<Card flush>
		<CardHeader divided title={visitorText.perGender} description={format(visitorText.genderNote, { count: formatNumber(data.with_gender, 0), total: formatNumber(data.total_transactions, 0) })} />
		{#if data.by_gender.length === 0}
			<Notice text={visitorText.noData} />
		{:else}
			<DataTable sort={visitor.genderSort} columns={groupColumns} rows={data.by_gender} rowKey={(row) => row.label} trailing="omzet" />
		{/if}
	</Card>
	<Card flush>
		<CardHeader divided title={visitorText.perCategory} description={format(visitorText.categoryNote, { count: formatNumber(data.with_category, 0), total: formatNumber(data.total_transactions, 0) })} />
		{#if data.by_category.length === 0}
			<Notice text={visitorText.noData} />
		{:else}
			<DataTable sort={visitor.categorySort} columns={groupColumns} rows={data.by_category} rowKey={(row) => row.label} trailing="omzet" />
		{/if}
	</Card>
</div>

<Card>
	<CardHeader
		class="mb-4"
		title={visitorText.trendTitle}
		description={visitor.metric === 'omzet' ? visitorText.dailyRevenue : format(visitorText.stackedBy, { dimension: visitor.dimension })}
	/>
	<SeriesChart
		labels={data.days.map((day) => formatDayMonth(day.date))}
		{series}
		format={visitor.metric === 'omzet' ? undefined : (value) => formatNumber(value, 0)}
		tooltipFormat={visitor.metric === 'omzet' ? formatRupiah : (value) => format(visitorText.transactionCount, { count: formatNumber(value, 0) })}
		label={visitorText.chartSummary}
	/>
</Card>

<Card flush>
	<CardHeader divided title={visitorText.perDate} description={visitor.sort.param ? undefined : visitorText.newestFirst} />
	<DataTable sort={visitor.sort} columns={days} rows={data.table} rowKey={(row) => row.date} rowClass={(row) => (row.transactions === 0 ? QUIET_VALUE : '')}>
		{#snippet first(row)}
			{@const label = dayLabel(row.date)}
			<span class={label.sunday ? 'text-danger-500' : ''}>{label.weekday}</span>
			{label.day}
			{#if marker(row.date)}<Badge tone="brand">{marker(row.date)}</Badge>{/if}
		{/snippet}
	</DataTable>
</Card>

<p class="text-xs text-slate-500">
	{visitorText.footnote}
</p>
