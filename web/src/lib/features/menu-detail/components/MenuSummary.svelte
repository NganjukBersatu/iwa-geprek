<script lang="ts">
	import type { MenuItem } from '$lib/api/types';
	import FigureCards from '$lib/components/card/FigureCards.svelte';
	import { formatNumber, formatRupiah } from '$lib/format/currency';
	import { branches } from '$lib/stores/branch';
	import { termText } from '$lib/text/terms';
	import { menuDetailText } from '$lib/text/menu-detail';

	let { item, sellers }: { item: MenuItem; sellers: string } = $props();

	const soldOut = $derived(item.unavailable_outlet_ids.map((id) => $branches.find((outlet) => outlet.id === id)?.name ?? id));
	const percent = (value: string | null) => (value === null ? menuDetailText.followsBranch : `${formatNumber(value)}%`);

	const figures = $derived([
		{ label: termText.basePrice, value: formatRupiah(item.price) },
		{ label: menuDetailText.tax, value: percent(item.tax_percent) },
		{ label: menuDetailText.service, value: percent(item.service_percent) },
		{ label: menuDetailText.soldIn, value: sellers },
		{ label: menuDetailText.outOfStockAt, value: soldOut.length > 0 ? soldOut.join(', ') : menuDetailText.noBranch }
	]);
</script>

<FigureCards {figures} label={menuDetailText.summary} />
