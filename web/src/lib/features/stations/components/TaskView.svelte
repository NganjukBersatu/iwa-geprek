<script lang="ts">
	import { onMount } from 'svelte';
	import type { StationStep } from '$lib/api/types';
	import { live } from '$lib/live/live';
	import Banner from '$lib/components/card/Banner.svelte';
	import Card from '$lib/components/card/Card.svelte';
	import CardHeader from '$lib/components/card/CardHeader.svelte';
	import FigureList from '$lib/components/card/FigureList.svelte';
	import Notice from '$lib/components/card/Notice.svelte';
	import BackButton from '$lib/components/button/BackButton.svelte';
	import Button from '$lib/components/button/Button.svelte';
	import TextArea from '$lib/components/form/TextArea.svelte';
	import PageHeader from '$lib/components/header/PageHeader.svelte';
	import SkeletonPage from '$lib/components/skeleton/SkeletonPage.svelte';
	import DataTable from '$lib/components/table/DataTable.svelte';
	import type { Column } from '$lib/components/table/types';
	import { formatDateTime } from '$lib/format/datetime';
	import { PAGES } from '$lib/nav/pages';
	import { formatTarget, KIND_LABEL, STAGE_LABEL, STEP_LABEL } from '../labels';
	import type { InterveneAction, TaskState } from '../task.svelte';
	import { termText } from '$lib/text/terms';
	import { actionText } from '$lib/text/actions';
	import { stationText } from '$lib/text/stations';
	import { format } from '$lib/text/format';

	let { task }: { task: TaskState } = $props();

	onMount(() => {
		void task.load();
		return live.on(task.tables, () => void task.load(true));
	});

	const ACTION_LABEL: Record<InterveneAction, string> = { start: stationText.advanceToProcessing, finish: stationText.advanceToFinished, undo: stationText.stepBack };
	const MAX_REASON = 255;

	const data = $derived(task.data);
	const stepColumns: Column<StationStep>[] = [
		{ key: 'langkah', label: stationText.step, align: 'left', value: (row) => (row.intervened ? format(stationText.stepIntervention, { step: STEP_LABEL[row.step] ?? row.step }) : (STEP_LABEL[row.step] ?? row.step)) },
		{ key: 'oleh', label: termText.by, align: 'left', value: (row) => row.by ?? stationText.system },
		{ key: 'alasan', label: stationText.reason, align: 'left', value: (row) => row.reason ?? '' },
		{ key: 'waktu', label: termText.time, align: 'left', value: (row) => formatDateTime(row.at) }
	];
	const blocked = $derived(data ? (data.voided ? stationText.orderCancelled : data.removed ? stationText.itemRemoved : data.locked ? stationText.orderCancelPending : '') : '');
</script>

<div class="flex flex-col gap-4 tablet:gap-6">
	<PageHeader title={data ? data.item : stationText.stationItem} description={data ? format(stationText.taskSubtitle, { station: data.station_name, branch: data.outlet_name, time: formatDateTime(data.order_created_at) }) : ''}>
		{#snippet leading()}
			<BackButton label={stationText.monitor} href={PAGES.stationMonitor.path} />
		{/snippet}
	</PageHeader>

	{#if task.error}
		<Banner tone="danger" icon="alert-triangle" title={stationText.itemLoadFailedTitle}>
			{task.error}
			{#snippet action()}
				<Button label={actionText.retry} onclick={() => void task.load()} />
			{/snippet}
		</Banner>
	{:else if task.loading && !data}
		<SkeletonPage label={stationText.itemLoading} />
	{:else if data}
		<div class="grid grid-cols-1 gap-4 laptop:grid-cols-2 tablet:gap-6">
			<div class="flex flex-col gap-4 tablet:gap-6">
				<Card>
					<CardHeader title={stationText.currentPosition} description={stationText.currentPositionDescription} icon="map-pin" />
					<div class="mt-4">
						<FigureList
							figures={[
								{ label: termText.order, value: [data.receipt_number ? `#${data.receipt_number}` : '', data.table_no ? format(stationText.tableNumber, { number: data.table_no }) : (data.customer_name ?? '')].filter(Boolean).join(' · ') },
								{ label: termText.station, value: `${data.station_name} (${KIND_LABEL[data.station_kind]})` },
								{ label: stationText.stage, value: STAGE_LABEL[data.stage] },
								{ label: stationText.target, value: formatTarget(data.target_seconds) },
								{ label: stationText.entered, value: data.arrived_at ? formatDateTime(data.arrived_at) : stationText.notArrived },
								{ label: stationText.started, value: data.started_at ? formatDateTime(data.started_at) : stationText.notYet },
								{ label: stationText.finished, value: data.finished_at ? formatDateTime(data.finished_at) : stationText.notYet },
								...(data.options.length > 0 || data.note ? [{ label: termText.note, value: [...data.options, data.note ?? ''].filter(Boolean).join(' · ') }] : [])
							]}
						/>
					</div>
				</Card>
				<Card flush>
					<CardHeader divided title={stationText.history} description={stationText.historyDescription} icon="history" />
					{#if data.steps.length === 0}
						<Notice text={stationText.noSteps} />
					{:else}
						<DataTable columns={stepColumns} rows={data.steps} rowKey={(row) => `${row.step}-${row.at}`} />
					{/if}
				</Card>
			</div>

			{#if task.canIntervene}
				<Card>
					<CardHeader title={stationText.intervention} description={stationText.interventionDescription} icon="hand-stop" tone="warning" />
					<div class="mt-4 flex flex-col gap-4">
						{#if blocked}
							<Notice text={blocked} />
						{:else if task.actions.length === 0}
							<Notice text={stationText.itemNotArrived} />
						{:else}
							<div class="flex flex-wrap gap-2">
								{#each task.actions as action (action)}
									<Button label={ACTION_LABEL[action]} active={task.action === action} onclick={() => task.choose(action)} />
								{/each}
							</div>
							<TextArea label={stationText.reason} bind:value={task.reason} rows={3} maxlength={MAX_REASON} placeholder={stationText.reasonExample} />
							{#if task.saveError}
								<Banner tone="danger" icon="alert-triangle">{task.saveError}</Banner>
							{/if}
							<div class="flex justify-end">
								<Button
									label={task.saving ? actionText.saving : stationText.saveIntervention}
									variant="primary"
									disabled={task.action === null || task.saving}
									onclick={() => void task.submit()}
								/>
							</div>
						{/if}
					</div>
				</Card>
			{/if}
		</div>
	{/if}
</div>
