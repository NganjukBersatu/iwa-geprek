<script lang="ts">
	import { controlText } from '$lib/text/controls';
	import { format } from '$lib/text/format';

	let {
		value = $bindable(1),
		label,
		min = 1,
		max = 99
	}: {
		value?: number;
		label: string;
		min?: number;
		max?: number;
	} = $props();

	const step = 'flex size-9 min-h-0 min-w-0 items-center justify-center text-slate-500 hover:bg-brand-soft hover:text-brand disabled:opacity-40 disabled:hover:bg-transparent';
</script>

<div role="group" aria-label={label} class="inline-flex items-center overflow-hidden rounded-md border border-slate-200 bg-white">
	<button type="button" class={step} disabled={value <= min} onclick={() => (value = Math.max(min, value - 1))} aria-label={format(controlText.decrease, { name: label })}>
		<i class="ti ti-minus" aria-hidden="true"></i>
	</button>
	<span class="min-w-8 text-center text-sm font-semibold text-slate-800" aria-live="polite">{value}</span>
	<button type="button" class={step} disabled={value >= max} onclick={() => (value = Math.min(max, value + 1))} aria-label={format(controlText.increase, { name: label })}>
		<i class="ti ti-plus" aria-hidden="true"></i>
	</button>
</div>
