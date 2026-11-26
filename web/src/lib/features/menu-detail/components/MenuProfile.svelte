<script lang="ts">
	import { menuText } from '$lib/text/menu';
	import { controlText } from '$lib/text/controls';
	import type { MenuItem } from '$lib/api/types';
	import Card from '$lib/components/card/Card.svelte';
	import FigureList from '$lib/components/card/FigureList.svelte';
	import { EMPTY_VALUE } from '$lib/format/currency';
	import { termText } from '$lib/text/terms';
	import { menuDetailText } from '$lib/text/menu-detail';
	import { format } from '$lib/text/format';

	let { item }: { item: MenuItem } = $props();
</script>

<Card flush>
	<div class="flex flex-col gap-3 bg-brand-soft p-4">
		<span class="text-xs font-medium text-brand-deep">{menuDetailText.photo}</span>
		<div class="flex aspect-4/3 w-full max-w-80 items-center justify-center overflow-hidden rounded-lg bg-brand-tint">
			{#if item.image_url}
				<img src={item.image_url} alt={format(controlText.photoOf, { name: item.name })} class="size-full object-cover" />
			{:else}
				<span class="flex flex-col items-center gap-2 text-xs text-brand-deep">
					<i class="ti ti-photo text-display" aria-hidden="true"></i>
					{menuDetailText.noPhoto}
				</span>
			{/if}
		</div>
	</div>
	<div class="flex flex-col gap-3 border-t border-brand-line p-4">
		<FigureList
			title={menuDetailText.information}
			figures={[
				{ label: termText.category, value: item.category_name ?? EMPTY_VALUE },
				{ label: menuText.availability, value: item.is_available ? menuText.available : termText.outOfStock }
			]}
		/>
		<section class="flex flex-col gap-1 border-t border-slate-100 pt-3 text-xs">
			<h3 class="font-semibold text-slate-600">{termText.description}</h3>
			<p class="whitespace-pre-line {item.description ? 'text-slate-700' : 'text-slate-500'}">{item.description ?? menuDetailText.noDescription}</p>
		</section>
	</div>
</Card>
