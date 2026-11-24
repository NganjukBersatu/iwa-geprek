<script lang="ts">
	import { EMPTY_VALUE } from '$lib/format/currency';
	import { formatClockRange, formatClockSpan } from '$lib/format/datetime';
	import Badge from './Badge.svelte';
	import { termText } from '$lib/text/terms';

	const DAY_OFF = termText.dayOff;

	let {
		start,
		end,
		dayOff = false,
		overtime = false
	}: {
		start: string | null | undefined;
		end: string | null | undefined;
		/** A day-off code has no hours; it shows as a grey "Libur". */
		dayOff?: boolean;
		/** Overtime hours take the overtime colour, so they never read as working hours. */
		overtime?: boolean;
	} = $props();

	const range = $derived(formatClockRange(start, end));
</script>

{#if dayOff}
	<Badge tone="neutral">{DAY_OFF}</Badge>
{:else if range && start && end}
	<Badge tone={overtime ? 'category' : 'info'} title="{range} ({formatClockSpan(start, end)})">{range} · {formatClockSpan(start, end)}</Badge>
{:else}
	<span class="text-slate-500">{EMPTY_VALUE}</span>
{/if}
