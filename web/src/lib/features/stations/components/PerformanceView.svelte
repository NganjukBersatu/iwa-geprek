<script lang="ts">
	import type { StationHour, StationUserTiming } from '$lib/api/types';
	import Card from '$lib/components/card/Card.svelte';
	import CardHeader from '$lib/components/card/CardHeader.svelte';
	import Notice from '$lib/components/card/Notice.svelte';
	import SummaryCard from '$lib/components/card/SummaryCard.svelte';
	import DataTable from '$lib/components/table/DataTable.svelte';
	import type { Column } from '$lib/components/table/types';
	import { formatNumber } from '$lib/format/currency';
	import { formatRatio, formatSeconds, timingCaption } from '../labels';
	import type { PerformanceData, PerformanceState } from '../performance.svelte';
	import { hour } from '../served-columns';
	import ServedTimesView from './ServedTimesView.svelte';
	import { termText } from '$lib/text/terms';
	import { stationText } from '$lib/text/stations';
	import { format } from '$lib/text/format';

	let { data, performance }: { data: PerformanceData; performance: PerformanceState } = $props();

	const overall = $derived(data.station.overall);
	const hourColumns: Column<StationHour>[] = [
		{ key: 'jam', label: termText.hour, value: (row) => hour(row.hour) },
		{ key: 'item', label: termText.item, value: (row) => formatNumber(row.tasks, 0) },
		{ key: 'menunggu', label: stationText.waiting, value: (row) => formatSeconds(row.average_wait_seconds) },
		{ key: 'pengerjaan', label: stationText.working, value: (row) => formatSeconds(row.average_work_seconds) },
		{ key: 'tepat', label: stationText.onTime, value: (row) => formatRatio(row.on_time_ratio) }
	];
	const userColumns: Column<StationUserTiming>[] = [
		{ key: 'karyawan', label: termText.employee, align: 'left', value: (row) => row.name || stationText.accountRemoved },
		{ key: 'stasiun', label: termText.station, align: 'left', value: (row) => row.station_name },
		{ key: 'item', label: termText.item, value: (row) => formatNumber(row.tasks, 0) },
		{ key: 'pengerjaan', label: stationText.average, value: (row) => formatSeconds(row.average_work_seconds) },
		{ key: 'tepat', label: stationText.onTime, value: (row) => formatRatio(row.on_time_ratio) }
	];
</script>

<div class="flex flex-col gap-4 tablet:gap-6">
	<div class="grid grid-cols-1 gap-4 tablet:grid-cols-3">
		<SummaryCard label={stationText.averageWaiting} caption={format(stationText.waitingCaptionWithTiming, { timing: timingCaption(overall) })} value={formatSeconds(overall.average_wait_seconds)} icon="hourglass" accent="primary" />
		<SummaryCard label={stationText.averageWorking} caption={stationText.workingCaption} value={formatSeconds(overall.average_work_seconds)} icon="tools-kitchen-2" accent="ink" />
		<SummaryCard label={stationText.onTime} caption={stationText.onTimeCaption} value={formatRatio(overall.on_time_ratio)} icon="target-arrow" accent="green" />
	</div>

	<div class="grid grid-cols-1 gap-4 laptop:grid-cols-2 tablet:gap-6">
		<Card flush>
			<CardHeader divided title={stationText.perHour} description={stationText.perHourDescription} icon="clock" />
			{#if data.station.by_hour.length === 0}
				<Notice text={stationText.noFinishedItems} />
			{:else}
				<DataTable columns={hourColumns} rows={data.station.by_hour} rowKey={(row) => String(row.hour)} />
			{/if}
		</Card>
		<Card flush>
			<CardHeader divided title={stationText.perEmployee} description={stationText.perEmployeeDescription} icon="users" />
			{#if data.station.by_user.length === 0}
				<Notice text={stationText.noFinishedItems} />
			{:else}
				<DataTable columns={userColumns} rows={data.station.by_user} rowKey={(row) => `${row.user_id ?? ''}-${row.station_id}`} />
			{/if}
		</Card>
	</div>

	<ServedTimesView data={data.kitchen} kitchen={performance} />
</div>
