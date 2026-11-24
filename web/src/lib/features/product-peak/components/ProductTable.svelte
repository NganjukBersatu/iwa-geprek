<script lang="ts">
	import Card from '$lib/components/card/Card.svelte';
	import CardHeader from '$lib/components/card/CardHeader.svelte';
	import Notice from '$lib/components/card/Notice.svelte';
	import Pager from '$lib/components/pager/Pager.svelte';
	import DataTable from '$lib/components/table/DataTable.svelte';
	import { productPeakColumns } from '../columns';
	import type { ProductPeakState } from '../peak.svelte';
	import { productPeakText } from '$lib/text/product-peak';
	import { format } from '$lib/text/format';

	let { peak }: { peak: ProductPeakState } = $props();

	const data = $derived(peak.data);
	const unitLower = $derived(peak.unitName.toLowerCase());
	const search = $derived(peak.query.search);
	const columns = $derived(productPeakColumns(peak.unitName));

</script>

{#if data}
	<Card flush>
		<CardHeader
			divided
			title={format(productPeakText.productDetailsPer, { unit: unitLower })}
			description={format(productPeakText.productRowsNote, { unit: unitLower, search: search ? ` · disaring \"${search}\"` : '' })}
		/>

		{#if data.rows.length === 0}
			<Notice text={search ? productPeakText.noMatch : productPeakText.noSales} />
		{:else}
			<DataTable {columns} rows={data.rows} rowKey={(row) => `${row.menu_item_name}|${row.key}`} trailing="omzet" loading={peak.loading} />

			<div class="border-t border-slate-100 px-4 pb-4 tablet:px-5">
				<Pager page={data.page} total={data.total_rows} unit="baris" disabled={peak.loading} onchange={(page) => peak.setPage(page)} />
			</div>
		{/if}
	</Card>

	<p class="text-note text-slate-500">
		{format(productPeakText.productTableNote, { unit: unitLower })}
	</p>
{/if}
