<script lang="ts">
	import { sparklineOptions } from '$lib/charts/theme';
	import Chart from './Chart.svelte';
	import { controlText } from '$lib/text/controls';

	/** The colour comes from the text colour of `class`, so a card's tone colours its trend without a second palette. */
	let { values, class: className = '' }: { values: number[]; class?: string } = $props();

	let holder = $state<HTMLDivElement | null>(null);
	let color = $state('');

	// Read again whenever the class changes, so a card that changes tone redraws in its new colour.
	$effect(() => {
		void className;
		if (holder) color = getComputedStyle(holder).color;
	});

	const options = $derived(color ? sparklineOptions(values, color) : null);
</script>

{#if values.length}
	<div bind:this={holder} class="block w-full {className}" aria-hidden="true">
		{#if options}<Chart {options} label={controlText.trend} class="h-full" />{/if}
	</div>
{/if}
