<script lang="ts">
	import { dynamicStyle } from '$lib/platform/dynamic-style';
	import AppIcon from '$lib/components/icon/AppIcon.svelte';
	import type { IconName } from '$lib/theme/icons';
	import type { CardTone } from './types';

	const DECORATION_SIZE_FRACTION = 0.78;
	const DECORATION_OFFSET_X_FRACTION = 0.14;
	const DECORATION_OFFSET_Y_FRACTION = 0.06;
	const DECORATION_TILT = -12;
	const DECORATION_ALPHA = 0.13;
	/** Kartu lebih pendek dari sekian kali tinggi badge memakai susunan berdampingan. */
	const COMPACT_HEIGHT_FACTOR = 2.2;
	const CONTROL = 40;
	const MD = 12;

	/** Kartu satu fitur: badge ikon di atas, judul di bawah, hiasan ikon di latar; seluruh kartu dapat disentuh. */
	let { title, icon, decoration, tone, href }: { title: string; icon: IconName; decoration: IconName; tone: CardTone; href: string } = $props();

	let height = $state(0);

	const dark = $derived(tone === 'primary' || tone === 'deep');
	const container = $derived({ primary: 'bg-primary', accent: 'bg-accent', soft: 'bg-surface-accent', deep: 'bg-content' }[tone]);
	const content = $derived(dark ? 'on-primary' : 'content');
	const compact = $derived(height < CONTROL * COMPACT_HEIGHT_FACTOR + MD * 2);
</script>

{#snippet badge()}
	<span class="flex shrink-0 items-center justify-center rounded-full {dark ? 'bg-on-primary-subtle' : ''}" use:dynamicStyle={{ width: `${CONTROL}px`, height: `${CONTROL}px`, 'background-color': dark ? undefined : 'rgb(255 255 255 / 0.45)' }}>
		<AppIcon {icon} tint={content} />
	</span>
{/snippet}

<a {href} class="relative block size-full overflow-hidden rounded-card {container}" bind:clientHeight={height}>
	<span
		class="pointer-events-none absolute"
		use:dynamicStyle={{ top: `${height * DECORATION_OFFSET_Y_FRACTION}px`, right: `${-height * DECORATION_OFFSET_X_FRACTION}px`, transform: `rotate(${DECORATION_TILT}deg)`, opacity: DECORATION_ALPHA }}
	>
		<AppIcon icon={decoration} tint={content} size={height * DECORATION_SIZE_FRACTION} />
	</span>
	{#if compact}
		<span class="relative flex size-full items-center gap-2 px-3">
			{@render badge()}
			<span class="text-title {dark ? 'text-on-primary' : 'text-content'}">{title}</span>
		</span>
	{:else}
		<span class="relative flex size-full flex-col justify-between p-3">
			{@render badge()}
			<span class="text-title {dark ? 'text-on-primary' : 'text-content'}">{title}</span>
		</span>
	{/if}
</a>
