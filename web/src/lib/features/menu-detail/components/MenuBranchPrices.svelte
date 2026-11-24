<script lang="ts">
	import type { MenuItem } from '$lib/api/types';
	import Card from '$lib/components/card/Card.svelte';
	import CardHeader from '$lib/components/card/CardHeader.svelte';
	import { branchPriceOf, sellsAt, type BranchOption } from '$lib/components/form/branch-prices.svelte';
	import DataTable from '$lib/components/table/DataTable.svelte';
	import type { Column } from '$lib/components/table/types';
	import { formatRupiah } from '$lib/format/currency';
	import { termText } from '$lib/text/terms';
	import { menuDetailText } from '$lib/text/menu-detail';

	let { item, outlets }: { item: MenuItem; outlets: BranchOption[] } = $props();

	const columns: Column<BranchOption>[] = [
		{ key: 'cabang', label: termText.branch, align: 'left', value: (branch) => branch.name },
		{ key: 'status', label: menuDetailText.saleStatus, align: 'left', value: (branch) => (sellsAt(item, branch.id) ? menuDetailText.onSale : menuDetailText.notOnSale), class: (branch) => (sellsAt(item, branch.id) ? '' : 'text-slate-500') },
		{ key: 'sumber', label: menuDetailText.priceSource, align: 'left', value: (branch) => (branchPriceOf(item, branch.id).own ? menuDetailText.branchPrice : termText.basePrice) },
		{ key: 'harga', label: termText.price, value: (branch) => formatRupiah(branchPriceOf(item, branch.id).price), class: () => 'font-semibold' }
	];
</script>

<Card flush>
	<CardHeader divided title={menuDetailText.pricePerBranch} description={menuDetailText.basePriceNote} />
	<DataTable {columns} rows={outlets} rowKey={(branch) => branch.id} trailing="harga" />
</Card>
