<script lang="ts">
	import type { CategorySales } from '$lib/api/types';
	import Badge from '$lib/components/card/Badge.svelte';
	import { EMPTY_VALUE, formatRupiah } from '$lib/format/currency';
	import { categoryReportText } from '$lib/text/category-report';
	import { format } from '$lib/text/format';
	import { changeText } from '../columns';

	let { row }: { row: CategorySales } = $props();

	const percent = $derived(row.revenue_change_percent === null ? null : Number(row.revenue_change_percent));
	const text = $derived(changeText(row));
	const tone = $derived(percent === null || percent === 0 ? 'neutral' : percent > 0 ? 'success' : 'danger');
	const icon = $derived(percent === null ? null : percent > 0 ? 'arrow-up-right' : percent < 0 ? 'arrow-down-right' : 'minus');
</script>

{#if text === EMPTY_VALUE}
	{text}
{:else}
	<Badge {tone} title={format(categoryReportText.previousPeriodRevenue, { amount: formatRupiah(row.previous_revenue) })}>
		{#if icon}<i class="ti ti-{icon}" aria-hidden="true"></i>{/if}
		{text}
	</Badge>
{/if}
