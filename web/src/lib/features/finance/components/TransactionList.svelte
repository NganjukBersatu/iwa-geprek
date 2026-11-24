<script lang="ts">
	import Button from '$lib/components/button/Button.svelte';
	import Badge from '$lib/components/card/Badge.svelte';
	import Banner from '$lib/components/card/Banner.svelte';
	import Card from '$lib/components/card/Card.svelte';
	import CardHeader from '$lib/components/card/CardHeader.svelte';
	import SkeletonList from '$lib/components/skeleton/SkeletonList.svelte';
	import Notice from '$lib/components/card/Notice.svelte';
	import Pager from '$lib/components/pager/Pager.svelte';
	import DataTable from '$lib/components/table/DataTable.svelte';
	import { formatDate } from '$lib/date/range';
	import { formatRupiah } from '$lib/format/currency';
	import { transactionColumns } from '../columns';
	import type { OverviewState } from '../overview.svelte';
	import { financeText } from '$lib/text/finance';
	import { format } from '$lib/text/format';
	import { termText } from '$lib/text/terms';

	let { overview }: { overview: OverviewState } = $props();

	const list = $derived(overview.transactions);
	const report = $derived(list.report);

	const scopeText = $derived(list.focusDate ? formatDate(list.focusDate) : overview.periodLabel);
	const methodLabel = $derived(list.methods.find((method) => method.code === list.method)?.label);
	const groupLabel = $derived(list.group === 'cash' ? financeText.cash : termText.nonCash);
	const columns = transactionColumns;

</script>

<Card flush>
	<CardHeader divided title={financeText.transactionsTitle} description={format(financeText.filteredCaption, { scope: scopeText })}>
		{#snippet actions()}
			{#if list.focusDate}
				<Button label={financeText.wholeRange} icon="x" onclick={() => list.focus(null)} />
			{/if}
		{/snippet}
	</CardHeader>

	{#if list.error}
		<div class="p-4 tablet:p-5">
			<Banner tone="danger" icon="alert-triangle">{list.error}</Banner>
		</div>
	{/if}

	{#if !report}
		{#if list.loading}<SkeletonList rows={5} label={financeText.transactionsLoading} />{/if}
	{:else}
		<div class="flex flex-wrap items-baseline justify-between gap-x-4 gap-y-1 bg-slate-50 px-4 py-3 tablet:px-5">
			<p class="text-xs text-slate-500">
				<b class="text-slate-800">{report.count}</b> {financeText.transactionsLabel}
				{#if list.method}· {methodLabel ?? list.method}{:else if list.group !== 'all'}· {groupLabel}{/if}
			</p>
			<p class="text-sm font-semibold text-brand">{formatRupiah(report.amount)}</p>
		</div>

		{#if report.rows.length === 0}
			<Notice text={financeText.noTransactionsMatch} />
		{:else}
			<DataTable sort={list.sort} {columns} rows={report.rows} rowKey={(row) => row.id} rowClass={(row) => (row.voided ? 'opacity-60' : '')} trailing="total" loading={list.loading}>
				{#snippet cell(row, column)}
					{#if column.key === 'metode'}
						<Badge>{row.voided ? financeText.voidedPrefix : ''}{column.value(row)}</Badge>
					{:else}
						{column.value(row)}
					{/if}
				{/snippet}
			</DataTable>

			<div class="border-t border-slate-100 px-4 pb-4 tablet:px-5">
				<Pager page={report.page} total={report.count} unit="transaksi" disabled={list.loading} onchange={(page) => list.setPage(page)} />
			</div>
		{/if}
	{/if}
</Card>
