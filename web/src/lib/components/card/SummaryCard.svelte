<script lang="ts">
	import { dynamicStyle } from '$lib/motion/actions';
	import type { Snippet } from 'svelte';
	import { summaryText } from '$lib/text/summary';
	import NumberTicker from '../motion/NumberTicker.svelte';
	import { summaryAccents, type SummaryAccent } from './summary-accent';

	let {
		label,
		caption,
		value,
		icon,
		accent,
		expanded,
		order,
		onclick,
		delta,
		aside,
		extra,
		class: className = ''
	}: {
		label: string;
		caption: string;
		value: string;
		icon: string;
		accent: SummaryAccent;
		/** Only a card that opens a detail has this; the others are plain figures. */
		expanded?: boolean;
		order?: number;
		onclick?: () => void;
		delta?: Snippet;
		/** A figure at the right end of the caption line, level with the caption. */
		aside?: Snippet;
		/** Smaller lines under the caption, such as a split of the figure. */
		extra?: Snippet;
		class?: string;
	} = $props();

	const colours = $derived(summaryAccents[accent]);
	const footed = $derived(!!delta || !!onclick);
</script>

<svelte:element
	this={onclick ? 'button' : 'div'}
	role={onclick ? 'button' : undefined}
	type={onclick ? 'button' : undefined}
	{onclick}
	aria-expanded={onclick && expanded !== undefined ? expanded : undefined}
	use:dynamicStyle={{ order }}
	class="flex w-full min-w-0 flex-col gap-1 rounded-lg border p-3.5 text-left {onclick ? 'transition-shadow hover:border-brand hover:shadow-md motion-reduce:transition-none' : ''} {colours.surface} {expanded ? 'border-brand ring-1 ring-brand' : ''} {className}"
>
	<span class="flex items-center gap-2.5">
		<span class="flex size-7 shrink-0 items-center justify-center rounded-md {colours.solid}">
			<i class="ti ti-{icon} text-base" aria-hidden="true"></i>
		</span>
		<span class="text-sm font-semibold text-brand-ink">{label}</span>
	</span>
	<span class="text-xl font-semibold text-brand-ink"><NumberTicker text={value} /></span>
	<span class="flex items-center justify-between gap-2">
		<span class="text-xs text-brand-muted">{caption}</span>
		{#if aside}{@render aside()}{/if}
	</span>
	{#if extra}
		<span class="flex flex-col gap-1">{@render extra()}</span>
	{/if}
	{#if footed}
		<span class="mt-1 flex flex-wrap items-center justify-between gap-2 border-t border-brand-ink/10 pt-2">
			{#if delta}{@render delta()}{/if}
			{#if onclick}
				<span class="ml-auto inline-flex items-center gap-1 text-xs font-semibold text-brand">
					{expanded ? summaryText.closeDetail : summaryText.openDetail}
					<i class="ti ti-chevron-down text-sm transition-transform duration-200 motion-reduce:transition-none {expanded ? 'rotate-180' : ''}" aria-hidden="true"></i>
				</span>
			{/if}
		</span>
	{/if}
</svelte:element>
