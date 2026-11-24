<script lang="ts">
	import type { Snippet } from 'svelte';
	import { tones, type Tone } from './tone';

	let {
		tone = 'info',
		icon = 'info-circle',
		title,
		children,
		action
	}: {
		tone?: Tone;
		icon?: string;
		title?: string;
		children?: Snippet;
		action?: Snippet;
	} = $props();
</script>

<div class="flex items-start gap-2.5 rounded-lg border p-3 {tones[tone].banner}" role={tone === 'danger' ? 'alert' : 'status'}>
	<i class="ti ti-{icon} text-base" aria-hidden="true"></i>
	<div class="min-w-0 flex-1 text-xs">
		{#if title}
			<p class="font-semibold">{title}</p>
		{/if}
		{#if children}
			<div class="leading-4 {title ? 'mt-0.5' : ''}">{@render children()}</div>
		{/if}
	</div>
	{#if action}
		<div class="shrink-0">{@render action()}</div>
	{/if}
</div>
