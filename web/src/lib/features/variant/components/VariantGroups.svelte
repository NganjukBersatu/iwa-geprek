<script lang="ts">
	import Card from '$lib/components/card/Card.svelte';
	import CardHeader from '$lib/components/card/CardHeader.svelte';
	import Notice from '$lib/components/card/Notice.svelte';
	import ShareBar from '$lib/components/chart/ShareBar.svelte';
	import DataTable from '$lib/components/table/DataTable.svelte';
	import { variantColumns } from '../columns';
	import type { VariantState } from '../variant.svelte';
	import { variantReportText } from '$lib/text/variant-report';
	import { format } from '$lib/text/format';

	let { variant }: { variant: VariantState } = $props();

	const columns = $derived(variantColumns(variant.variants?.by_menu ?? false));
</script>

{#if variant.groups.length === 0}
	<Card><Notice class="px-0!" title={variantReportText.noVariantsSold} text={variantReportText.noVariantsSoldHint} /></Card>
{:else}
	{#each variant.groups as [group, rows] (group)}
		<Card flush>
			<CardHeader class="border-b border-slate-100 bg-slate-50 p-4 tablet:px-5" title={group} description={format(variantReportText.choicesCount, { count: rows.length })} />
			<DataTable sort={variant.variantSort} {columns} {rows} rowKey={(row) => row.option + (row.menu ?? '')} trailing="omzet">
				{#snippet first(row)}
					{row.option}{#if row.menu}<span class="font-normal text-slate-500"> · {row.menu}</span>{/if}
				{/snippet}
				{#snippet cell(row, column)}
					{#if column.key === 'persen'}
						<span class="flex items-center gap-2">
							<ShareBar value={Number(row.portions_percent)} class="w-24 shrink-0" />
							<span class="text-slate-500">{column.value(row)}</span>
						</span>
					{:else}
						{column.value(row)}
					{/if}
				{/snippet}
			</DataTable>
		</Card>
	{/each}
	<p class="text-xs text-slate-500">
		{variantReportText.variantsNote}
	</p>
{/if}
