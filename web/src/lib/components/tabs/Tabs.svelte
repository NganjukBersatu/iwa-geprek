<script lang="ts">
	import { dynamicStyle } from '$lib/motion/actions';
	import type { Snippet } from 'svelte';

	type Tab = { key: string; label: string; count?: number; icon?: string };

	let {
		tabs,
		value = $bindable(''),
		label,
		variant = 'line',
		actions,
		class: className = ''
	}: {
		tabs: Tab[];
		value?: string;
		label: string;
		/** `line` is the underlined bar above a panel, `pill` the row of rounded buttons used on open pages. */
		variant?: 'line' | 'pill';
		actions?: Snippet;
		class?: string;
	} = $props();

	const index = $derived(Math.max(0, tabs.findIndex((tab) => tab.key === value)));
</script>

{#if variant === 'pill'}
	<div role="tablist" aria-label={label} class="flex flex-wrap gap-2 {className}">
		{#each tabs as tab (tab.key)}
			<button
				type="button"
				role="tab"
				aria-selected={tab.key === value}
				onclick={() => (value = tab.key)}
				class="inline-flex items-center gap-2 rounded-full border border-brand-line px-4 py-2 text-sm font-semibold transition hover:-translate-y-0.5 motion-reduce:transition-none {tab.key === value ? 'border-2 border-brand bg-brand text-brand-on' : 'bg-white text-brand-deep'}"
			>
				{#if tab.icon}<i class="ti ti-{tab.icon}" aria-hidden="true"></i>{/if}
				{tab.label}
			</button>
		{/each}
	</div>
{:else}
	<div class="flex flex-wrap items-center justify-between gap-2 border-b border-slate-200 px-3 {className}">
		<div role="tablist" aria-label={label} class="relative inline-grid grid-flow-col auto-cols-fr">
			{#each tabs as tab (tab.key)}
				<button
					type="button"
					role="tab"
					aria-selected={tab.key === value}
					onclick={() => (value = tab.key)}
					class="flex min-h-12 items-center justify-center gap-2 min-w-[8.5rem] whitespace-nowrap px-4 text-sm tablet:min-w-[11rem] transition-colors motion-reduce:transition-none {tab.key === value ? 'font-semibold text-brand' : 'font-semibold text-slate-500 hover:text-brand'}"
				>
					{tab.label}
					{#if tab.count !== undefined}
						<span class="rounded-full px-2 text-xs transition-colors motion-reduce:transition-none {tab.key === value ? 'bg-brand text-white' : 'bg-slate-100 text-slate-500'}">{tab.count}</span>
					{/if}
				</button>
			{/each}
			<span
				aria-hidden="true"
				class="absolute -bottom-px left-0 h-0.5 rounded-t bg-brand transition-transform duration-300 ease-out motion-reduce:transition-none"
				use:dynamicStyle={{ width: `calc(100% / ${tabs.length})`, transform: `translateX(${index * 100}%)` }}
			></span>
		</div>
		{#if actions}
			<div class="flex items-center gap-2 py-1">{@render actions()}</div>
		{/if}
	</div>
{/if}
