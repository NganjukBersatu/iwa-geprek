<script lang="ts">
	import { dynamicStyle } from '$lib/platform/dynamic-style';
	import AppIcon from '$lib/components/icon/AppIcon.svelte';
	import { t } from '$lib/text/t';
	import type { BottomBarItem } from './types';

	const PROMINENT_OVERHANG = 22;
	const PROMINENT_SIZE = 56;
	const PROMINENT_RING = 3;
	const INDICATOR_WIDTH = 56;
	const INDICATOR_HEIGHT = 30;

	let { items }: { items: readonly BottomBarItem[] } = $props();

	const overhang = $derived(items.some((item) => item.prominent) ? PROMINENT_OVERHANG : 0);
</script>

<nav class="relative w-full" aria-label={t('web_navigation_main')}>
	<div class="absolute inset-x-0 bottom-0 border-t border-divider bg-surface" use:dynamicStyle={{ top: `${overhang}px` }}></div>
	<div class="relative flex items-end px-1 py-1" use:dynamicStyle={{ 'padding-bottom': 'calc(4px + var(--safe-bottom))' }}>
		{#each items as item (item.href)}
			{@const tint = item.selected ? 'text-primary' : 'text-content-muted'}
			<a
				href={item.href}
				aria-current={item.selected ? 'page' : undefined}
				class="flex min-h-[var(--space-touch)] flex-1 flex-col items-center py-1 {item.prominent ? '' : 'rounded-field'}"
			>
				{#if item.prominent}
					<span class="flex items-center justify-center rounded-full bg-background" use:dynamicStyle={{ width: `${PROMINENT_SIZE}px`, height: `${PROMINENT_SIZE}px`, padding: `${PROMINENT_RING}px` }}>
						<span class="flex size-full items-center justify-center rounded-full bg-primary"><AppIcon icon={item.icon} tint="on-primary" size={28} /></span>
					</span>
				{:else}
					<span
						class="flex items-center justify-center rounded-full {item.selected ? 'bg-selected' : ''}"
						use:dynamicStyle={{ width: `${INDICATOR_WIDTH}px`, height: `${INDICATOR_HEIGHT}px` }}
					>
						<AppIcon icon={item.icon} tint={item.selected ? 'primary' : 'content-muted'} />
					</span>
				{/if}
				<span class="text-caption w-full truncate text-center {tint} {item.selected ? 'font-bold' : ''}">{item.label}</span>
			</a>
		{/each}
	</div>
</nav>
