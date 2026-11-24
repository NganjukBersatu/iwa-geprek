<script lang="ts">
	import type { Snippet } from 'svelte';

	/** A form field that opens a panel to choose from, for choices too many or too rich for a plain dropdown. */
	let {
		label,
		summary,
		chosen,
		open = $bindable(false),
		hint,
		children
	}: {
		label: string;
		/** What the closed field shows: the current choice, or what to do when there is none. */
		summary: string;
		/** False greys the summary, which then reads as a prompt. */
		chosen: boolean;
		open?: boolean;
		hint?: string;
		children: Snippet;
	} = $props();

	const id = $props.id();
	let trigger = $state<HTMLButtonElement>();

	// Esc closes the open panel and returns to the field, without also closing the dialog around it.
	function keydown(event: KeyboardEvent): void {
		if (event.key !== 'Escape' || !open) return;
		event.preventDefault();
		event.stopPropagation();
		open = false;
		trigger?.focus();
	}
</script>

<div class="flex flex-col gap-1" role="presentation" onkeydown={keydown}>
	<label for={id} class="text-xs font-semibold text-slate-600">{label}</label>
	<button
		{id}
		bind:this={trigger}
		type="button"
		aria-expanded={open}
		onclick={() => (open = !open)}
		class="flex w-full items-center justify-between gap-2 rounded-md border border-slate-200 bg-white px-3 py-2 text-left text-sm text-slate-800 focus:border-brand focus:outline-none focus:ring-2 focus:ring-brand-line"
	>
		<span class="truncate {chosen ? '' : 'text-slate-500'}">{summary}</span>
		<i class="ti {open ? 'ti-chevron-up' : 'ti-chevron-down'} text-slate-400" aria-hidden="true"></i>
	</button>
	{#if open}
		<div class="flex flex-col gap-2 rounded-md border border-slate-200 bg-slate-50 p-2">{@render children()}</div>
	{/if}
	{#if hint}
		<p class="text-xs text-slate-500">{hint}</p>
	{/if}
</div>
