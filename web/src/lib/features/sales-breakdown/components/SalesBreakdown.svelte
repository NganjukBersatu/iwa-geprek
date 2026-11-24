<script lang="ts">
	import { onMount } from 'svelte';
	import Button from '$lib/components/button/Button.svelte';
	import Banner from '$lib/components/card/Banner.svelte';
	import Card from '$lib/components/card/Card.svelte';
	import CardHeader from '$lib/components/card/CardHeader.svelte';
	import Notice from '$lib/components/card/Notice.svelte';
	import DataTable from '$lib/components/table/DataTable.svelte';
	import { live } from '$lib/live/live';
	import { SALES_TABLES } from '$lib/live/tables';
	import { whenChanged } from '$lib/stores/when-changed.svelte';
	import { actionText } from '$lib/text/actions';
	import { format } from '$lib/text/format';
	import { salesBreakdownText } from '$lib/text/sales-breakdown';
	import type { ReportQuery } from '../../report/report.svelte';
	import { SalesBreakdownState } from '../breakdown.svelte';
	import { orderTypeColumns, outletColumns } from '../columns';

	let { query, periodLabel }: { query: ReportQuery; periodLabel: string } = $props();

	const breakdown = new SalesBreakdownState(() => query);

	whenChanged(() => query, (next) => void breakdown.load(next));

	onMount(() => live.on(SALES_TABLES, () => void breakdown.load(breakdown.query, true)));
</script>

{#if breakdown.error}
	<Banner tone="danger" icon="alert-triangle" title={salesBreakdownText.loadFailedTitle}>
		{breakdown.error}
		{#snippet action()}
			<Button label={actionText.retry} onclick={() => void breakdown.load()} />
		{/snippet}
	</Banner>
{:else if breakdown.loading && !breakdown.data}
	<Card flush>
		<Notice loading text={salesBreakdownText.loading} />
	</Card>
{:else if breakdown.data}
	<Card flush>
		<CardHeader divided title={salesBreakdownText.perOrderType} description={format(salesBreakdownText.perOrderTypeCaption, { period: periodLabel })} />
		{#if breakdown.data.order_types.length === 0}
			<Notice text={salesBreakdownText.noSales} />
		{:else}
			<DataTable sort={breakdown.typeSort} columns={orderTypeColumns} rows={breakdown.data.order_types} rowKey={(row) => row.key} trailing="omzet" />
		{/if}
	</Card>

	{#if breakdown.data.outlets.length > 0}
		<Card flush>
			<CardHeader divided title={salesBreakdownText.perBranch} description={format(salesBreakdownText.perBranchCaption, { period: periodLabel })} />
			<DataTable sort={breakdown.outletSort} columns={outletColumns} rows={breakdown.data.outlets} rowKey={(row) => row.key} trailing="omzet" />
		</Card>
	{/if}
{/if}
