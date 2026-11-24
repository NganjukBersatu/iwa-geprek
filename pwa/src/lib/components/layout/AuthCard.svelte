<script lang="ts">
	import { dynamicStyle } from '$lib/platform/dynamic-style';
	import type { Snippet } from 'svelte';
	import { viewport } from '$lib/platform/viewport.svelte';

	const WIDE_CARD_MAX_WIDTH = 900;
	const WIDE_CARD_HEIGHT = 550;
	const NARROW_CARD_MAX_WIDTH = 420;
	const BANNER_HEIGHT = 140;
	const BANNER_HEIGHT_TINY = 110;
	const BANNER_CURVE_HEIGHT = 30;
	const CARD_SHADOW = '0 20px 25px -5px rgb(0 0 0 / 0.25), 0 8px 10px -6px rgb(0 0 0 / 0.25)';

	/** Kartu masuk: gambar merek di samping (layar lebar) atau di atas dengan tepi bawah melengkung (HP), formulir di panel hijau. */
	let { brandImage, brandDescription, content }: { brandImage: string; brandDescription: string; content: Snippet<[boolean]> } = $props();

	const wide = $derived(viewport.isWide);
	const tiny = $derived(viewport.size === 'tiny');
	const wideFormPadding = $derived(viewport.size === 'medium' ? '34px 32px' : '60px');
	const narrowFormPadding = $derived(tiny ? '24px 16px' : '32px 24px 28px 24px');
</script>

<div class="relative h-full w-full overflow-y-auto bg-background" use:dynamicStyle={{ padding: 'var(--safe-top) var(--safe-right) var(--safe-bottom) var(--safe-left)' }}>
	<div class="flex min-h-full flex-col items-center justify-center" use:dynamicStyle={{ padding: 'var(--page-padding)' }}>
		{#if wide}
			<div
				class="flex w-[95%] overflow-hidden rounded-card bg-primary"
				use:dynamicStyle={{ 'max-width': `${WIDE_CARD_MAX_WIDTH}px`, height: `${WIDE_CARD_HEIGHT}px`, 'box-shadow': CARD_SHADOW }}
			>
				<img src={brandImage} alt={brandDescription} class="h-full w-1/2 object-cover" />
				<div class="flex h-full w-1/2 flex-col justify-center overflow-y-auto" use:dynamicStyle={{ padding: wideFormPadding }}>
					{@render content(true)}
				</div>
			</div>
		{:else}
			<div class="w-full overflow-hidden rounded-card bg-primary" use:dynamicStyle={{ 'max-width': `${NARROW_CARD_MAX_WIDTH}px`, 'box-shadow': CARD_SHADOW }}>
				<img
					src={brandImage}
					alt={brandDescription}
					class="w-full object-cover"
					use:dynamicStyle={{ height: `${tiny ? BANNER_HEIGHT_TINY : BANNER_HEIGHT}px`, 'object-position': '50% 30%', 'border-bottom-left-radius': `40% ${BANNER_CURVE_HEIGHT}px`, 'border-bottom-right-radius': `40% ${BANNER_CURVE_HEIGHT}px` }}
				/>
				<div use:dynamicStyle={{ padding: narrowFormPadding }}>
					{@render content(false)}
				</div>
			</div>
		{/if}
	</div>
</div>
