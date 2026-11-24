<script lang="ts">
	import NumberTicker from '../motion/NumberTicker.svelte';
	import { tones, type Tone } from './tone';

	let {
		label,
		value,
		note,
		tone = 'neutral',
		negative = false
	}: {
		label: string;
		value: string;
		note?: string;
		tone?: Tone;
		negative?: boolean;
	} = $props();

	const surface: Record<Tone, string> = {
		brand: 'border-brand-line bg-brand-page',
		accent: 'border-brand-accent-line bg-brand-accent-soft',
		success: 'border-success-200 bg-success-50',
		info: 'border-info-200 bg-info-50',
		category: 'border-category-200 bg-category-50',
		danger: 'border-danger-200 bg-danger-50',
		warning: 'border-warning-200 bg-warning-50',
		neutral: 'border-slate-200 bg-white'
	};
</script>

<div class="rounded-lg border p-4 {surface[tone]}">
	<p class="text-xs font-semibold {tones[tone].ink}">{label}</p>
	<p class="mt-1 text-xl font-semibold {negative ? 'text-danger-700' : 'text-slate-800'}"><NumberTicker text={value} /></p>
	{#if note}
		<p class="text-xs text-slate-500">{note}</p>
	{/if}
</div>
