<script lang="ts">
	import type { Snippet } from 'svelte';
	import FilterButton from './FilterButton.svelte';
	import FilterChips from './FilterChips.svelte';
	import type { Filters } from './filters.svelte';
	import SearchBox from './SearchBox.svelte';
	import { controlText } from '$lib/text/controls';
	import { format } from '$lib/text/format';

	let {
		value = '',
		placeholder,
		label,
		filters,
		shown,
		total,
		unit,
		onsearch,
		actions
	}: {
		value?: string;
		placeholder: string;
		label: string;
		filters: Filters;
		shown: number;
		total: number;
		unit: string;
		onsearch: (query: string) => void;
		actions?: Snippet;
	} = $props();
</script>

<div class="flex flex-col gap-3 border-b border-slate-100 p-4 tablet:p-5">
	<div class="flex flex-wrap items-center gap-3">
		<SearchBox {value} {placeholder} {label} {onsearch} class="w-full tablet:max-w-sm" />
		<FilterButton {filters} />
		{#if actions}{@render actions()}{/if}
		<span class="text-xs text-slate-500 tablet:ml-auto">{format(controlText.showingOf, { shown: shown, total: total, unit: unit })}</span>
	</div>
	<FilterChips {filters} />
</div>
