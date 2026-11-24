<script lang="ts">
	import type { KitchenReport } from '$lib/api/types';
	import Badge from '$lib/components/card/Badge.svelte';
	import Card from '$lib/components/card/Card.svelte';
	import CardHeader from '$lib/components/card/CardHeader.svelte';
	import Notice from '$lib/components/card/Notice.svelte';
	import SummaryCard from '$lib/components/card/SummaryCard.svelte';
	import ShareBar from '$lib/components/chart/ShareBar.svelte';
	import DataTable from '$lib/components/table/DataTable.svelte';
	import { EMPTY_VALUE, formatNumber } from '$lib/format/currency';
	import { hour, hourColumns, minutes, orderColumns } from '../served-columns';
	import type { PerformanceState } from '../performance.svelte';
	import { stationText } from '$lib/text/stations';
	import { format } from '$lib/text/format';

	let { data, kitchen }: { data: KitchenReport; kitchen: PerformanceState } = $props();

	const percent = (value: string | null) => (value === null ? EMPTY_VALUE : `${formatNumber(value, 1)}%`);

	const busiest = $derived(data.busiest_hour);
	const max = $derived(Math.max(1, ...data.by_hour.map((row) => Number(row.average_minutes))));
	const late = (row: { average_minutes: string }) => Number(row.average_minutes) > data.threshold_minutes;

	const hours = $derived(hourColumns(late));
</script>

<div class="grid grid-cols-1 gap-4 tablet:grid-cols-2 laptop:grid-cols-4">
	<SummaryCard label={stationText.average} caption={format(stationText.medianAndLongest, { median: minutes(data.median_minutes), longest: minutes(data.max_minutes) })} value={minutes(data.average_minutes)} icon="clock" accent="primary" />
	<SummaryCard
		label={stationText.finishedOrders}
		caption={data.unserved_count > 0 ? format(stationText.stillOnBoard, { count: data.unserved_count }) : 'semua sudah selesai'}
		value={formatNumber(data.served_count, 0)}
		icon="checks"
		accent="ink"
	/>
	<SummaryCard
		label={format(stationText.lateMoreThanMinutes, { minutes: data.threshold_minutes })}
		caption={format(stationText.ofFinished, { percent: percent(data.late_percent) })}
		value={formatNumber(data.late, 0)}
		icon="alarm"
		accent="red"
	/>
	<SummaryCard
		label={stationText.busiestHour}
		caption={busiest ? format(stationText.ordersAverage, { count: busiest.count, average: minutes(busiest.average_minutes) }) : stationText.noData}
		value={busiest ? hour(busiest.hour) : EMPTY_VALUE}
		icon="flame"
		accent="accent"
	/>
</div>

<div class="grid grid-cols-1 gap-4 laptop:grid-cols-2 tablet:gap-6">
	<Card flush>
		<CardHeader divided title={stationText.perEntryHour} description={stationText.redBarMeaning} />
		{#if data.by_hour.length === 0}
			<Notice text={stationText.noFinishedOrders} />
		{:else}
			<DataTable sort={kitchen.hourSort} columns={hours} rows={data.by_hour} rowKey={(row) => String(row.hour)} trailing="rata">
				{#snippet first(row)}
					<span class="block">{hour(row.hour)}</span>
					<ShareBar value={(Number(row.average_minutes) / max) * 100} tone={late(row) ? 'danger' : 'brand'} class="mt-1.5" />
				{/snippet}
			</DataTable>
		{/if}
	</Card>

	<Card flush>
		<CardHeader divided title={stationText.slowestOrdersTitle} description={stationText.slowestOrdersDescription} />
		{#if data.slowest.length === 0}
			<Notice text={stationText.noFinishedOrders} />
		{:else}
			<DataTable sort={kitchen.orderSort} columns={orderColumns} rows={data.slowest} rowKey={(row) => row.order_id} trailing="menit">
				{#snippet cell(row, column)}
					{#if column.key === 'menit'}
						<Badge tone={Number(row.minutes) > data.threshold_minutes ? 'danger' : 'neutral'}>{column.value(row)}</Badge>
					{:else}
						{column.value(row)}
					{/if}
				{/snippet}
			</DataTable>
		{/if}
	</Card>
</div>
