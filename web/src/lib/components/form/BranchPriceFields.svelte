<script lang="ts">
	import CheckRow from './CheckRow.svelte';
	import MoneyField from './MoneyField.svelte';
	import type { BranchOption, BranchPriceForm } from './branch-prices.svelte';
	import { controlText } from '$lib/text/controls';
	import { format } from '$lib/text/format';

	let {
		form,
		outlets,
		everywhereLabel,
		hint
	}: {
		form: BranchPriceForm;
		outlets: BranchOption[];
		everywhereLabel: string;
		hint: string;
	} = $props();
</script>

<section class="flex flex-col gap-2">
	<h3 class="text-xs font-semibold text-slate-600">{controlText.branchesAndPrices}</h3>
	<CheckRow label={everywhereLabel} checked={form.everywhere} onchange={() => form.toggleEverywhere()} />
	<div class="flex flex-col gap-2">
		{#each outlets as outlet (outlet.id)}
			<div class="grid items-center gap-2 tablet:grid-cols-[1fr_12rem]">
				{#if form.everywhere}
					<span class="text-sm text-slate-700">{outlet.name}</span>
				{:else}
					<CheckRow label={outlet.name} checked={form.sells(outlet.id)} onchange={() => form.toggleSeller(outlet.id)} />
				{/if}
				<MoneyField label={format(controlText.priceAtBranch, { name: outlet.name })} bind:value={() => form.priceOf(outlet.id), (value) => form.setPrice(outlet.id, value)} />
			</div>
		{/each}
	</div>
	<p class="text-xs text-slate-500">{hint}</p>
</section>
