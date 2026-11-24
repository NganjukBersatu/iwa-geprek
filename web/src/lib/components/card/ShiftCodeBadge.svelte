<script lang="ts">
	import { dynamicStyle } from '$lib/motion/actions';
	import { formatClockRange } from '$lib/format/datetime';
	import { termText } from '$lib/text/terms';
	import { scheduleText } from '$lib/text/schedule';

	type Code = { code: string; color: string | null; start_clock: string | null; end_clock: string | null; is_day_off?: boolean };

	let { code, showTime = false }: { code: Code | undefined; showTime?: boolean } = $props();

	const hours = $derived(code?.is_day_off ? termText.dayOff : formatClockRange(code?.start_clock, code?.end_clock));
</script>

{#if code}
	<span class="inline-flex flex-wrap items-center gap-x-1.5 gap-y-0.5">
		<span
			class="inline-flex items-center gap-1.5 rounded-lg border px-2 py-0.5 text-xs font-semibold text-slate-800 {code.color ? '' : 'border-slate-200 bg-slate-50'}"
			use:dynamicStyle={{ 'background-color': code.color ? `color-mix(in oklab, ${code.color} 22%, white)` : undefined, 'border-color': code.color }}
			title={hours || undefined}
		>
			<span class="size-2.5 rounded-full bg-slate-300" use:dynamicStyle={{ 'background-color': code.color }}></span>{code.code}
		</span>
		{#if showTime && hours}<span class="text-xs text-slate-500">{hours}</span>{/if}
	</span>
{:else}
	<span class="text-xs text-slate-500">{scheduleText.noCode}</span>
{/if}
