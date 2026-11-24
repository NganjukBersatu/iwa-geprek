<script lang="ts">
	import { controlText } from '$lib/text/controls';
	import { onMount } from 'svelte';
	import { access } from '$lib/auth/access.svelte';
	import Button from '$lib/components/button/Button.svelte';
	import Badge from '$lib/components/card/Badge.svelte';
	import Banner from '$lib/components/card/Banner.svelte';
	import Card from '$lib/components/card/Card.svelte';
	import CardHeader from '$lib/components/card/CardHeader.svelte';
	import MetricTile from '$lib/components/card/MetricTile.svelte';
	import Notice from '$lib/components/card/Notice.svelte';
	import ConfirmDialog from '$lib/components/dialog/ConfirmDialog.svelte';
	import ListToolbar from '$lib/components/filter/ListToolbar.svelte';
	import TextField from '$lib/components/form/TextField.svelte';
	import PageHeader from '$lib/components/header/PageHeader.svelte';
	import { pageOf } from '$lib/components/pager/page-of';
	import Pager from '$lib/components/pager/Pager.svelte';
	import DataTable from '$lib/components/table/DataTable.svelte';
	import { EMPTY_VALUE, formatNumber } from '$lib/format/currency';
	import { formatDateTime } from '$lib/format/datetime';
	import { live } from '$lib/live/live';
	import { STOCK_TABLES } from '$lib/live/tables';
	import { PAGES } from '$lib/nav/pages';
	import { changeColumns, detailColumns, lineStatus, STATUS_LABELS, STATUS_TONES } from '../columns';
	import type { IngredientCountDetailState } from '../ingredient-count-detail.svelte';
	import { termText } from '$lib/text/terms';
	import { actionText } from '$lib/text/actions';
	import { ingredientCountDetailText } from '$lib/text/ingredient-count-detail';
	import { format } from '$lib/text/format';

	const LIST_PATH = PAGES.ingredientCounts.path;

	let { count }: { count: IngredientCountDetailState } = $props();

	const canCorrect = $derived(access.allows('correct_stock'));
	const detail = $derived(count.detail);
	let page = $state(1);
	const shown = $derived(pageOf(count.visibleRows, page));
	const period = $derived(detail ? `${detail.start} – ${detail.end}` : '');


	onMount(() => {
		void count.load();
		return live.on(STOCK_TABLES, () => void count.refresh());
	});
</script>

{#if count.error}
	<Banner tone="danger" icon="alert-triangle" title={ingredientCountDetailText.loadFailedTitle}>
		{count.error}
		{#snippet action()}
			<Button label={actionText.retry} variant="danger" onclick={() => void count.load()} />
		{/snippet}
	</Banner>
{:else if detail}
	<div class="flex flex-col gap-4 tablet:gap-6">
		<PageHeader title={format(ingredientCountDetailText.countTitle, { period: period })} description={format(ingredientCountDetailText.closedByFrom, { time: detail.user_name ?? EMPTY_VALUE, source: detail.source === 'tablet' ? 'tablet' : 'web', user: formatDateTime(detail.created_at) })}>
			{#snippet leading()}
				<Button label={ingredientCountDetailText.stockCount} icon="arrow-left" compact href={LIST_PATH} />
			{/snippet}
			{#snippet actions()}
				<Badge tone="danger">{termText.closed}</Badge>
				{#if canCorrect && count.ownPeriod}
					<Button label={actionText.edit} icon="pencil" active={count.bulk} disabled={count.busy} onclick={() => (count.bulk ? count.stopBulk() : count.startBulk())} />
					<Button label={ingredientCountDetailText.cancel} icon="arrow-back-up" variant="danger" disabled={count.busy} onclick={() => count.askCancel()} />
				{/if}
			{/snippet}
		</PageHeader>

		{#if count.actionError && !count.cancelling}
			<Banner tone="danger" icon="alert-triangle">{count.actionError}</Banner>
		{/if}

		<div class="grid grid-cols-2 gap-3 laptop:grid-cols-4">
			<MetricTile tone="brand" label={ingredientCountDetailText.countedIngredients} value={formatNumber(count.countedTotal, 0)} note="dari {formatNumber(count.rows.length, 0)} bahan aktif" />
			<MetricTile label={ingredientCountDetailText.notCounted} value={formatNumber(count.uncountedRows.length, 0)} note={count.ownPeriod ? ingredientCountDetailText.stillResetNote : ingredientCountDetailText.partNotCountedNote} />
			<MetricTile tone="warning" label={ingredientCountDetailText.hasDifference} value={formatNumber(count.differenceTotal, 0)} note="dari {formatNumber(count.countedTotal, 0)} yang dihitung" />
			<MetricTile label={ingredientCountDetailText.resetToZero} value={formatNumber(count.ownPeriod ? count.resetTotal : 0, 0)} note={count.ownPeriod ? ingredientCountDetailText.resetNote : ingredientCountDetailText.partCarriesNote} />
		</div>

		<Card flush>
			<CardHeader
				divided
				title={ingredientCountDetailText.perIngredient}
				description={format(count.ownPeriod ? ingredientCountDetailText.countColumnsNote : ingredientCountDetailText.partColumnsNote, { note: detail.note ? format(ingredientCountDetailText.notePrefix, { note: detail.note }) : '' })}
			/>
			<ListToolbar
				value={count.search}
				placeholder={ingredientCountDetailText.searchPlaceholder}
				label={ingredientCountDetailText.search}
				filters={count.filters}
				shown={shown.rows.length}
				total={count.visibleRows.length}
				unit="bahan"
				onsearch={(query) => {
					count.search = query;
					page = 1;
				}}
			/>
			{#if count.visibleRows.length === 0}
				<Notice text={ingredientCountDetailText.noMatch} />
			{:else}
				<DataTable columns={detailColumns} rows={shown.rows} rowKey={(row) => row.ingredient_id} loading={count.loading} trailing="status">
					{#snippet cell(row, column)}
						{#if column.key === 'status'}
							<Badge tone={STATUS_TONES[lineStatus(row)]}>{STATUS_LABELS[lineStatus(row)]}</Badge>
						{:else if column.key === 'real' && count.bulk}
							<div class="ml-auto w-24">
								<TextField
									compact
									label={format(controlText.countedOf, { name: row.name })}
									inputmode="decimal"
									placeholder={row.counted === null ? EMPTY_VALUE : String(Number(row.counted))}
									bind:value={() => count.edited[row.ingredient_id] ?? '', (typed) => (count.edited[row.ingredient_id] = typed)}
								/>
							</div>
						{:else}
							{column.value(row)}
						{/if}
					{/snippet}
				</DataTable>
			{/if}
			<div class="border-t border-slate-100 px-4 pb-4 tablet:px-5">
				<Pager page={shown.page} total={count.visibleRows.length} unit="bahan" list="rincian-opname" disabled={count.loading} onchange={(next) => (page = next)} />
			</div>
			{#if count.bulk}
				<div class="flex flex-wrap items-center gap-3 border-t border-slate-100 px-4 py-4 tablet:px-5">
					<span class="mr-auto text-xs text-slate-500">{format(ingredientCountDetailText.ingredientsChanged, { count: formatNumber(count.editedCount, 0) })}</span>
					<Button label={actionText.cancel} disabled={count.busy} onclick={() => count.stopBulk()} />
					<Button label={count.busy ? actionText.saving : ingredientCountDetailText.saveChanges} variant="primary" disabled={count.busy || count.editedCount === 0} onclick={() => void count.saveBulk()} />
				</div>
			{/if}
		</Card>

		{#if count.ownPeriod}
			<Card flush>
				<CardHeader divided title={ingredientCountDetailText.historyTitle} description={ingredientCountDetailText.historyDescription} />
				{#if !count.changes || count.changes.total === 0}
					<Notice text={ingredientCountDetailText.noChanges} />
				{:else}
					<DataTable sort={count.changeSort} columns={changeColumns} rows={count.changes.items} rowKey={(row) => row.id} loading={count.loading} />
					<div class="border-t border-slate-100 px-4 pb-4 tablet:px-5">
						<Pager page={count.changes.page} total={count.changes.total} unit="perubahan" list="perubahan-opname" disabled={count.loading} onchange={(next) => void count.loadChanges(next)} />
					</div>
				{/if}
			</Card>
		{/if}
	</div>
{:else}
	<Notice loading text={ingredientCountDetailText.loading} />
{/if}


<ConfirmDialog
	open={count.cancelling}
	title={format(ingredientCountDetailText.cancelCountTitle, { period: period })}
	confirmLabel="Batalkan opname"
	danger
	busy={count.busy}
	error={count.actionError}
	onconfirm={() => void count.confirmCancel()}
	oncancel={() => count.closeDialogs()}
>
	{ingredientCountDetailText.cancelNote}
</ConfirmDialog>
