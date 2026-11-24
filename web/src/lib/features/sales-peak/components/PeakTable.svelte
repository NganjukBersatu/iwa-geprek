<script lang="ts">
	import { QUIET_VALUE } from '$lib/components/table/quiet-value';
	import Badge from '$lib/components/card/Badge.svelte';
	import Card from '$lib/components/card/Card.svelte';
	import CardHeader from '$lib/components/card/CardHeader.svelte';
	import DataTable from '$lib/components/table/DataTable.svelte';
	import { peakColumns } from '../columns';
	import type { SalesPeakState } from '../peak.svelte';
	import { salesPeakText } from '$lib/text/sales-peak';
	import { format } from '$lib/text/format';

	let { peak }: { peak: SalesPeakState } = $props();

	const data = $derived(peak.data);
	const top = $derived(peak.salesHighlight?.peak_label);

	const columns = $derived(peakColumns(peak.unitName));
</script>

{#if data}
	<Card flush>
		<CardHeader
			divided
			title={format(salesPeakText.detailsPer, { unit: peak.unitName.toLowerCase() })}
			description={format(salesPeakText.rowsAndDays, { rows: data.rows.length, days: data.days })}
		/>

		<DataTable
			sort={peak.sort}
			{columns}
			rows={data.table}
			rowKey={(row) => row.key}
			highlight={(row) => (row.label === top ? 'warning' : false)}
			rowClass={(row) => (row.transactions === 0 ? QUIET_VALUE : '')}
			trailing="penjualan"
		>
			{#snippet first(row)}
				{row.label}
				{#if row.label === top}<Badge tone="warning">{salesPeakText.peak}</Badge>{/if}
			{/snippet}
		</DataTable>
	</Card>

	<p class="text-xs text-slate-500">
		{salesPeakText.percentNote}
	</p>
{/if}
