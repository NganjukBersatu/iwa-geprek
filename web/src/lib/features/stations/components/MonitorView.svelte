<script lang="ts">
	import { controlText } from '$lib/text/controls';
	import { goto } from '$app/navigation';
	import { onMount } from 'svelte';
	import { live } from '$lib/live/live';
	import { loadBranchOptions } from '$lib/stores/branch';
	import { whenChanged } from '$lib/stores/when-changed.svelte';
	import type { StationLateTask, StationMonitorBranch } from '$lib/api/types';
	import Banner from '$lib/components/card/Banner.svelte';
	import Card from '$lib/components/card/Card.svelte';
	import CardHeader from '$lib/components/card/CardHeader.svelte';
	import Notice from '$lib/components/card/Notice.svelte';
	import SummaryCard from '$lib/components/card/SummaryCard.svelte';
	import Button from '$lib/components/button/Button.svelte';
	import FilterButton from '$lib/components/filter/FilterButton.svelte';
	import FilterChips from '$lib/components/filter/FilterChips.svelte';
	import PageHeader from '$lib/components/header/PageHeader.svelte';
	import SkeletonPage from '$lib/components/skeleton/SkeletonPage.svelte';
	import DataTable from '$lib/components/table/DataTable.svelte';
	import type { Column } from '$lib/components/table/types';
	import { formatNumber } from '$lib/format/currency';
	import { stationTaskPath } from '$lib/nav/pages';
	import { formatSeconds, STAGE_LABEL } from '../labels';
	import type { MonitorState } from '../monitor.svelte';
	import { termText } from '$lib/text/terms';
	import { actionText } from '$lib/text/actions';
	import { stationText } from '$lib/text/stations';
	import { format } from '$lib/text/format';

	let { monitor }: { monitor: MonitorState } = $props();

	whenChanged(() => monitor.branch, () => void monitor.load());
	onMount(() => {
		void loadBranchOptions().then((options) => monitor.filters.setOptions('cabang', options));
		return live.on(monitor.tables, () => void monitor.refresh());
	});

	const data = $derived(monitor.data);
	const stations = $derived(data?.stations ?? []);
	const lateColumns: Column<StationLateTask>[] = [
		{ key: 'pesanan', label: termText.order, align: 'left', value: (row) => [row.receipt_number ? `#${row.receipt_number}` : '', row.table_no ? format(controlText.tableNumberLabel, { number: row.table_no }) : row.customer_name ?? ''].filter(Boolean).join(' · ') },
		{ key: 'cabang', label: termText.branch, align: 'left', value: (row) => row.outlet_name },
		{ key: 'stasiun', label: termText.station, align: 'left', value: (row) => row.station_name },
		{ key: 'item', label: termText.item, align: 'left', value: (row) => row.item },
		{ key: 'tahap', label: stationText.stage, align: 'left', value: (row) => STAGE_LABEL[row.stage] },
		{ key: 'terlambat', label: stationText.late, value: (row) => formatSeconds(row.late_seconds), class: () => 'font-semibold text-danger-700' }
	];
	const branchColumns = $derived<Column<StationMonitorBranch>[]>([
		{ key: 'cabang', label: termText.branch, align: 'left', value: (row) => row.outlet_name },
		...stations.map((station) => ({
			key: station.id,
			label: station.name,
			value: (row: StationMonitorBranch) => {
				const cell = row.cells.find((entry) => entry.station_id === station.id);
				if (!cell) return '0';
				return cell.late > 0 ? format(stationText.workingWithLate, { working: cell.working, late: cell.late }) : String(cell.working);
			},
			class: (row: StationMonitorBranch) => (row.cells.some((entry) => entry.station_id === station.id && entry.late > 0) ? 'font-semibold text-danger-700' : '')
		}))
	]);
</script>

<div class="flex flex-col gap-4 tablet:gap-6">
	<PageHeader title={stationText.monitorTitle} description={stationText.monitorDescription}>
		{#snippet actions()}
			<FilterButton filters={monitor.filters} />
		{/snippet}
	</PageHeader>

	<FilterChips filters={monitor.filters} />

	{#if monitor.error}
		<Banner tone="danger" icon="alert-triangle" title={stationText.monitorLoadFailedTitle}>
			{monitor.error}
			{#snippet action()}
				<Button label={actionText.retry} onclick={() => void monitor.load()} />
			{/snippet}
		</Banner>
	{:else if monitor.loading && !data}
		<SkeletonPage label={stationText.monitorLoading} />
	{:else if data}
		<div class="grid grid-cols-1 gap-4 tablet:grid-cols-2">
			<SummaryCard label={stationText.inProgress} caption={stationText.inProgressCaption} value={formatNumber(data.working, 0)} icon="tools-kitchen-2" accent="primary" />
			<SummaryCard label={stationText.lateNow} caption={stationText.lateNowCaption} value={formatNumber(data.late, 0)} icon="alarm" accent="red" />
		</div>

		<Card flush>
			<CardHeader divided title={stationText.lateItemsTitle} description={stationText.lateItemsDescription} icon="alarm" tone="danger" />
			{#if data.late_tasks.length === 0}
				<Notice text={stationText.noLateItems} />
			{:else}
				<DataTable columns={lateColumns} rows={data.late_tasks} rowKey={(row) => row.task_id} onopen={(row) => void goto(stationTaskPath(row.task_id))} />
			{/if}
		</Card>

		<Card flush>
			<CardHeader divided title={stationText.perBranch} description={stationText.perBranchDescription} icon="building-store" />
			{#if data.branches.length === 0}
				<Notice text={stationText.noBranchInScope} />
			{:else}
				<DataTable columns={branchColumns} rows={data.branches} rowKey={(row) => row.outlet_id}>
					{#snippet first(row)}
						<span class="flex items-center gap-2">{row.outlet_name}</span>
					{/snippet}
				</DataTable>
			{/if}
		</Card>
	{/if}
</div>
