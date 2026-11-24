<script lang="ts">
	import { onDestroy } from 'svelte';
	import { controlText } from '$lib/text/controls';

	let {
		value = $bindable(''),
		placeholder = controlText.searchPlaceholder,
		label = controlText.search,
		delay = 250,
		onsearch,
		class: className = ''
	}: {
		value?: string;
		placeholder?: string;
		label?: string;
		delay?: number;
		onsearch?: (query: string) => void;
		class?: string;
	} = $props();

	let timer: ReturnType<typeof setTimeout> | undefined;

	function emit(query: string): void {
		clearTimeout(timer);
		if (delay <= 0) {
			onsearch?.(query);
			return;
		}
		timer = setTimeout(() => onsearch?.(query), delay);
	}

	function handleInput(event: Event): void {
		value = (event.currentTarget as HTMLInputElement).value;
		emit(value);
	}

	function clear(): void {
		value = '';
		clearTimeout(timer);
		onsearch?.('');
	}

	onDestroy(() => clearTimeout(timer));
</script>

<div class="relative {className}">
	<i class="ti ti-search pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" aria-hidden="true"></i>
	<input
		type="text"
		inputmode="search"
		enterkeyhint="search"
		autocomplete="off"
		{placeholder}
		aria-label={label}
		{value}
		oninput={handleInput}
		class="w-full rounded-md border border-slate-200 bg-white py-2 pl-9 pr-9 text-sm outline-none focus:border-brand"
	/>
	{#if value}
		<button
			type="button"
			onclick={clear}
			aria-label={controlText.clearSearch}
			class="absolute right-1 top-1/2 flex size-7 min-h-0 min-w-0 -translate-y-1/2 items-center justify-center rounded-md text-slate-500 hover:bg-slate-100 hover:text-slate-600"
		>
			<i class="ti ti-x" aria-hidden="true"></i>
		</button>
	{/if}
</div>
