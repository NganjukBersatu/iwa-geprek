<script lang="ts">
	import type { Snippet } from 'svelte';
	import IconTile from './IconTile.svelte';
	import type { Tone } from './tone';

	let {
		title,
		description,
		icon,
		tone = 'brand',
		actions,
		divided = false,
		class: className = ''
	}: {
		title: string;
		description?: string;
		icon?: string;
		tone?: Tone;
		actions?: Snippet;
		divided?: boolean;
		class?: string;
	} = $props();
</script>

<header class="flex items-start justify-between gap-3 {divided ? 'border-b border-slate-100 p-4 tablet:p-5' : ''} {className}">
	<div class="min-w-0">
		<h2 class="font-semibold text-slate-800">{title}</h2>
		{#if description}
			<p class="mt-1 text-xs text-slate-500">{description}</p>
		{/if}
	</div>
	<div class="flex shrink-0 items-center gap-2">
		{#if actions}
			{@render actions()}
		{/if}
		{#if icon}
			<IconTile {icon} {tone} size="sm" />
		{/if}
	</div>
</header>
