<script lang="ts">
	import { todayIso } from '$lib/date/range';
	import { onMount } from 'svelte';
	import Badge from '$lib/components/card/Badge.svelte';
	import Banner from '$lib/components/card/Banner.svelte';
	import Button from '$lib/components/button/Button.svelte';
	import Card from '$lib/components/card/Card.svelte';
	import CardHeader from '$lib/components/card/CardHeader.svelte';
	import ConfirmDialog from '$lib/components/dialog/ConfirmDialog.svelte';
	import MetricTile from '$lib/components/card/MetricTile.svelte';
	import Notice from '$lib/components/card/Notice.svelte';
	import TextField from '$lib/components/form/TextField.svelte';
	import PageHeader from '$lib/components/header/PageHeader.svelte';
	import { pageOf } from '$lib/components/pager/page-of';
	import Pager from '$lib/components/pager/Pager.svelte';
	import DataTable from '$lib/components/table/DataTable.svelte';
	import { formatDate } from '$lib/date/range';
	import { EMPTY_VALUE, formatNumber } from '$lib/format/currency';
	import { formatDateTime } from '$lib/format/datetime';
	import { live } from '$lib/live/live';
	import { PAGES } from '$lib/nav/pages';
	import { actionText } from '$lib/text/actions';
	import { controlText } from '$lib/text/controls';
	import { format } from '$lib/text/format';
	import { ingredientCountRequestText as text } from '$lib/text/ingredient-count-requests';
	import { sheetColumns } from '../../ingredient-counts/columns';
	import CountDifference from '../../ingredient-counts/components/CountDifference.svelte';
	import type { IngredientCountRequestDetailState } from '../ingredient-count-request-detail.svelte';
	import RequestProgress from './RequestProgress.svelte';

	let { request }: { request: IngredientCountRequestDetailState } = $props();

	let page = $state(1);
	const shown = $derived(pageOf(request.rows, page));

	onMount(() => {
		void request.load();
		return live.on(['ingredient_count_requests', 'ingredients', 'ingredient_cards'], () => void request.refresh());
	});
</script>

{#if request.error}
	<Banner tone="danger" icon="alert-triangle" title={text.loadFailedTitle}>
		{request.error}
		{#snippet action()}
			<Button label={actionText.retry} variant="danger" onclick={() => void request.load()} />
		{/snippet}
	</Banner>
{:else if request.request}
	{@const item = request.request}
	<div class="flex flex-col gap-4 tablet:gap-6">
		<PageHeader
			title={format(text.pageTitle, { branch: item.outlet_name })}
			description={format(text.pageDescription, { from: formatDate(item.close_start), to: formatDate(item.close_end), name: item.requested_by ?? EMPTY_VALUE, time: formatDateTime(item.created_at) })}
		>
			{#snippet leading()}
				<Button label={PAGES.ingredientCounts.label} icon="arrow-left" compact href={PAGES.ingredientCounts.path} />
			{/snippet}
			{#snippet actions()}
				<Badge tone="warning">{text.requestedBadge}</Badge>
				<Button label={request.busy ? text.closing : text.closeAction} icon="lock" variant="primary" disabled={request.busy} onclick={() => request.askClose()} />
				<Button label={text.rejectAction} icon="x" variant="danger" disabled={request.busy} onclick={() => request.askReject()} />
			{/snippet}
		</PageHeader>

		<Card>
			<CardHeader title={text.history} />
			<div class="px-4 pb-4 tablet:px-5"><RequestProgress request={item} /></div>
		</Card>

		{#if request.actionError && !request.closing}
			<Banner tone="danger" icon="alert-triangle">{request.actionError}</Banner>
		{/if}

		<div class="grid grid-cols-2 gap-3 laptop:grid-cols-4">
			<MetricTile tone="brand" label={text.tileOpening} value={formatNumber(item.opening_filled, 0)} note={format(text.tileOpeningNote, { total: formatNumber(item.opening_total, 0) })} />
			<MetricTile label={text.tileCounted} value={formatNumber(request.filled, 0)} note={text.tileCountedNote} />
			<MetricTile tone="warning" label={text.tileDifference} value={formatNumber(request.differenceTotal, 0)} note={format(text.tileDifferenceNote, { count: formatNumber(request.filled, 0) })} />
			<MetricTile label={text.tileReset} value={formatNumber(request.resetTotal, 0)} note={text.tileResetNote} />
		</div>

		<Card flush>
			<CardHeader divided title={text.sheetTitle} description={`${item.note ? format(text.userNote, { note: item.note }) : ''}${text.sheetDescription}`} />
			{#if request.rows.length === 0}
				<Notice text={text.noIngredients} />
			{:else}
				<DataTable columns={sheetColumns} rows={shown.rows} rowKey={(row) => row.ingredient_id} loading={request.loading} trailing="selisih">
					{#snippet cell(row, column)}
						{#if column.key === 'real'}
							<div class="ml-auto w-24">
								<TextField
									compact
									label={format(controlText.countedOf, { name: row.name })}
									inputmode="decimal"
									placeholder={EMPTY_VALUE}
									bind:value={() => request.counted[row.ingredient_id] ?? '', (typed) => request.type(row.ingredient_id, typed)}
								/>
							</div>
						{:else if column.key === 'selisih'}
							<CountDifference difference={request.difference(row.ingredient_id, row.closing_stock)} closing={row.closing_stock} />
						{:else}
							{column.value(row)}
						{/if}
					{/snippet}
				</DataTable>
				<div class="border-t border-slate-100 px-4 pb-4 tablet:px-5">
					<Pager page={shown.page} total={request.rows.length} unit="bahan" disabled={request.loading} onchange={(next) => (page = next)} />
				</div>
				<div class="border-t border-slate-100 px-4 py-3 tablet:px-5">
					<span class="text-xs {request.draftProblem ? 'text-danger-700' : 'text-slate-500'}" role={request.draftProblem ? 'alert' : 'status'}>
						{request.draftProblem || (request.draftSavedAt ? format(text.draftSaved, { time: request.draftSavedAt }) : text.draftAuto)}
					</span>
				</div>
			{/if}
		</Card>
	</div>

	<ConfirmDialog
		open={request.closing}
		title={format(text.closeTitle, { branch: item.outlet_name, range: request.period ? format(text.periodRange, { from: formatDate(request.period.start), to: formatDate(request.period.end) }) : '' })}
		confirmLabel={text.closeConfirm}
		busy={request.busy}
		error={request.actionError}
		onconfirm={() => void request.confirmClose()}
		oncancel={() => request.closeDialogs()}
	>
		<p>{format(text.closeNote, { count: request.filled })}</p>
		<div class="mt-3">
			<Banner tone="warning" icon="alert-triangle" title={text.closeBannerTitle}>
				<ul class="mt-1 list-disc space-y-0.5 pl-4">
					<li>{format(text.closeResetNote, { total: formatNumber(request.rows.length, 0), untouched: formatNumber(request.rows.length - request.filled, 0) })}</li>
					<li>{text.closeMenuNote}</li>
					{#if request.period && request.period.end === todayIso()}<li>{text.closeSameDayNote}</li>{/if}
					<li>{text.closeResaleNote}</li>
					<li>{text.closeKeptNote}</li>
					<li>{format(text.closeDoneNote, { name: item.requested_by ?? EMPTY_VALUE })}</li>
				</ul>
			</Banner>
		</div>
	</ConfirmDialog>

	<ConfirmDialog
		open={request.rejecting}
		title={format(text.rejectTitle, { branch: item.outlet_name })}
		confirmLabel={text.rejectConfirm}
		danger
		busy={request.busy}
		error={request.actionError}
		onconfirm={() => void request.confirmReject()}
		oncancel={() => request.closeDialogs()}
	>
		<p>{format(text.rejectNote, { from: formatDate(item.close_start), to: formatDate(item.close_end), name: item.requested_by ?? EMPTY_VALUE })}</p>
		<p class="mt-2">{text.rejectSeen}</p>
	</ConfirmDialog>
{:else}
	<Notice loading text={text.loading} />
{/if}
