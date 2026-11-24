<script lang="ts">
	import { onMount } from 'svelte';
	import type { MenuTargetBranch, StationHour } from '$lib/api/types';
	import Banner from '$lib/components/card/Banner.svelte';
	import Card from '$lib/components/card/Card.svelte';
	import CardHeader from '$lib/components/card/CardHeader.svelte';
	import Notice from '$lib/components/card/Notice.svelte';
	import SummaryCard from '$lib/components/card/SummaryCard.svelte';
	import BackButton from '$lib/components/button/BackButton.svelte';
	import SaveButton from '$lib/components/button/SaveButton.svelte';
	import Button from '$lib/components/button/Button.svelte';
	import SelectField from '$lib/components/form/SelectField.svelte';
	import TextField from '$lib/components/form/TextField.svelte';
	import PageHeader from '$lib/components/header/PageHeader.svelte';
	import SkeletonPage from '$lib/components/skeleton/SkeletonPage.svelte';
	import DataTable from '$lib/components/table/DataTable.svelte';
	import type { Column } from '$lib/components/table/types';
	import { formatNumber } from '$lib/format/currency';
	import { live } from '$lib/live/live';
	import { PAGES } from '$lib/nav/pages';
	import { formatRatio, formatSeconds, formatTarget, timingCaption } from '../labels';
	import { hour } from '../served-columns';
	import type { TargetDetailState } from '../target-detail.svelte';
	import { termText } from '$lib/text/terms';
	import { actionText } from '$lib/text/actions';
	import { stationText } from '$lib/text/stations';
	import { format } from '$lib/text/format';

	let { target }: { target: TargetDetailState } = $props();

	onMount(() => {
		void target.load();
		return live.on(target.tables, () => void target.load(true));
	});

	const data = $derived(target.data);
	const branchColumns: Column<MenuTargetBranch>[] = [
		{ key: 'cabang', label: termText.branch, align: 'left', value: (row) => row.outlet_name },
		{ key: 'target', label: stationText.target, align: 'left', value: (row) => (row.target_seconds === null ? stationText.followsDefault : formatSeconds(row.target_seconds)) },
		{ key: 'rata', label: stationText.average, value: (row) => formatSeconds(row.average_work_seconds) },
		{ key: 'item', label: termText.item, value: (row) => formatNumber(row.tasks, 0) },
		{ key: 'tepat', label: stationText.onTime, value: (row) => formatRatio(row.on_time_ratio) }
	];
	const hourColumns: Column<StationHour>[] = [
		{ key: 'jam', label: termText.hour, value: (row) => hour(row.hour) },
		{ key: 'item', label: termText.item, value: (row) => formatNumber(row.tasks, 0) },
		{ key: 'rata', label: stationText.average, value: (row) => formatSeconds(row.average_work_seconds) },
		{ key: 'tepat', label: stationText.onTime, value: (row) => formatRatio(row.on_time_ratio) }
	];
	const branchOptions = $derived((data?.branches ?? []).map((row) => ({ value: row.outlet_id, label: row.outlet_name })));
</script>

<div class="flex flex-col gap-4 tablet:gap-6">
	<PageHeader title={data?.name ?? stationText.menuTarget} description={data ? format(stationText.targetFromStartToFinish, { station: data.station_name ?? stationText.noMakerStation }) : ''}>
		{#snippet leading()}
			<BackButton label={stationText.timeTarget} href={PAGES.stationTargets.path} />
		{/snippet}
	</PageHeader>

	{#if target.error}
		<Banner tone="danger" icon="alert-triangle" title={stationText.targetLoadFailedTitle}>
			{target.error}
			{#snippet action()}
				<Button label={actionText.retry} onclick={() => void target.load()} />
			{/snippet}
		</Banner>
	{:else if target.loading && !data}
		<SkeletonPage label={stationText.targetLoading} />
	{:else if data}
		<div class="grid grid-cols-1 gap-4 tablet:grid-cols-3">
			<SummaryCard label={stationText.averageWorking} caption={timingCaption(data.overall)} value={formatSeconds(data.overall.average_work_seconds)} icon="tools-kitchen-2" accent="primary" />
			<SummaryCard label={stationText.defaultTarget} caption={stationText.defaultTargetCaption} value={formatTarget(data.target_seconds)} icon="target-arrow" accent="ink" />
			<SummaryCard label={stationText.onTime} caption={stationText.onTimeTargetCaption} value={formatRatio(data.overall.on_time_ratio)} icon="clock-check" accent="green" />
		</div>

		{#if target.saveError}
			<Banner tone="danger" icon="alert-triangle">{target.saveError}</Banner>
		{/if}

		<div class="grid grid-cols-1 gap-4 laptop:grid-cols-2 tablet:gap-6">
			<Card>
				<CardHeader title={stationText.defaultTarget} description={stationText.defaultTargetHint} icon="target-arrow" />
				<div class="mt-4 grid grid-cols-2 gap-3">
					<TextField label={termText.hour} inputmode="numeric" bind:value={target.fallback.hours} maxlength={2} />
					<TextField label={stationText.minutes} inputmode="numeric" bind:value={target.fallback.minutes} maxlength={2} />
				</div>
				<div class="mt-4 flex justify-end">
					<SaveButton busy={target.saving} onclick={() => void target.saveFallback()} />
				</div>
			</Card>
			<Card>
				<CardHeader title={stationText.branchTarget} description={stationText.branchTargetHint} icon="building-store" />
				{#if branchOptions.length === 0}
					<div class="mt-4"><Notice text={stationText.noBranchInScope} /></div>
				{:else}
					<div class="mt-4 flex flex-col gap-3">
						<SelectField label={termText.branch} options={branchOptions} value={target.branchId} onchange={(value) => target.pickBranch(value)} />
						<div class="grid grid-cols-2 gap-3">
							<TextField label={termText.hour} inputmode="numeric" bind:value={target.branch.hours} maxlength={2} />
							<TextField label={stationText.minutes} inputmode="numeric" bind:value={target.branch.minutes} maxlength={2} />
						</div>
					</div>
					<div class="mt-4 flex justify-end">
						<SaveButton label={stationText.saveBranchTarget} busy={target.saving} onclick={() => void target.saveBranch()} />
					</div>
				{/if}
			</Card>
		</div>

		<div class="grid grid-cols-1 gap-4 laptop:grid-cols-2 tablet:gap-6">
			<Card flush>
				<CardHeader divided title={stationText.perBranch} description={stationText.currentMonthPeriod} icon="building-store" />
				<DataTable columns={branchColumns} rows={data.branches} rowKey={(row) => row.outlet_id} />
			</Card>
			<Card flush>
				<CardHeader divided title={stationText.perHour} description={stationText.menuPerHourDescription} icon="clock" />
				{#if data.by_hour.length === 0}
					<Notice text={stationText.noFinishedItems} />
				{:else}
					<DataTable columns={hourColumns} rows={data.by_hour} rowKey={(row) => String(row.hour)} />
				{/if}
			</Card>
		</div>
	{/if}
</div>
