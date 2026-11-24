<script lang="ts">
	import type { Snippet } from 'svelte';
	import { onMount, tick } from 'svelte';
	import AppIcon from '$lib/components/icon/AppIcon.svelte';
	import { animateValue } from '$lib/theme/animate';
	import { bgColor, type ColorToken } from '$lib/theme/colors';
	import { emphasized, QUICK_MILLIS, SLOW_MILLIS, STANDARD_MILLIS } from '$lib/theme/ease';
	import { portal } from '$lib/theme/portal';
	import { dynamicStyle } from '$lib/platform/dynamic-style';

	/** Radius kartu tertutup; sama dengan radius kartu tema, dianimasikan ke nol saat terbuka. */
	const CARD_RADIUS = 24;
	const RISE = 16;

	/**
	 * Kartu yang melebar menjadi layar penuh (mengisi pembungkus bertanda `data-expand-host`) saat ditekan dan kembali saat ditutup; bagian [head] selalu tampak
	 * dan [body] muncul setelah kartu melebar. Tanpa [body], menekan kartu hanya memanggil [onOpen].
	 */
	let {
		containerColor,
		actionColor,
		actionTint,
		openLabel,
		closeLabel,
		head,
		body,
		leading,
		padding = '16px',
		centered = false,
		fill = false,
		onOpen
	}: {
		containerColor: ColorToken | 'transparent';
		actionColor: ColorToken;
		actionTint: ColorToken;
		openLabel: string;
		closeLabel: string;
		/** Menerima true saat kartu sedang terbuka, supaya rincian tambahan hanya tampil di layar penuh. */
		head: Snippet<[boolean]>;
		body?: Snippet;
		leading?: Snippet;
		padding?: string;
		centered?: boolean;
		/** Mengisi tinggi pembungkusnya, untuk kartu di dalam petak berukuran tetap. */
		fill?: boolean;
		onOpen?: () => void;
	} = $props();

	type Box = { left: number; top: number; width: number; height: number };

	let card: HTMLDivElement | undefined = $state();
	let open = $state(false);
	let box = $state<Box>({ left: 0, top: 0, width: 0, height: 0 });
	let radius = $state(CARD_RADIUS);
	let bodyProgress = $state(0);
	let busy = false;

	const hostBox = (): Box => {
		const host = card?.closest('[data-expand-host]')?.getBoundingClientRect();
		return host ? { left: host.left, top: host.top, width: host.width, height: host.height } : { left: 0, top: 0, width: window.innerWidth, height: window.innerHeight };
	};

	const lerp = (a: number, b: number, p: number) => a + (b - a) * p;

	async function expand(): Promise<void> {
		if (!card || busy) return;
		busy = true;
		const from = card.getBoundingClientRect();
		const start: Box = { left: from.left, top: from.top, width: from.width, height: from.height };
		const end = hostBox();
		box = start;
		radius = CARD_RADIUS;
		bodyProgress = 0;
		open = true;
		await tick();
		await animateValue({
			from: 0,
			to: 1,
			durationMillis: SLOW_MILLIS,
			easing: emphasized,
			onUpdate: (p) => {
				box = { left: lerp(start.left, end.left, p), top: lerp(start.top, end.top, p), width: lerp(start.width, end.width, p), height: lerp(start.height, end.height, p) };
				radius = lerp(CARD_RADIUS, 0, p);
			}
		}).done;
		await animateValue({ from: 0, to: 1, durationMillis: STANDARD_MILLIS, easing: emphasized, onUpdate: (p) => (bodyProgress = p) }).done;
		busy = false;
	}

	async function collapse(): Promise<void> {
		if (!card || busy) return;
		busy = true;
		const target = card.getBoundingClientRect();
		const end: Box = { left: target.left, top: target.top, width: target.width, height: target.height };
		const start = box;
		await animateValue({ from: bodyProgress, to: 0, durationMillis: QUICK_MILLIS, easing: emphasized, onUpdate: (p) => (bodyProgress = p) }).done;
		await animateValue({
			from: 0,
			to: 1,
			durationMillis: SLOW_MILLIS,
			easing: emphasized,
			onUpdate: (p) => {
				box = { left: lerp(start.left, end.left, p), top: lerp(start.top, end.top, p), width: lerp(start.width, end.width, p), height: lerp(start.height, end.height, p) };
				radius = lerp(0, CARD_RADIUS, p);
			}
		}).done;
		open = false;
		busy = false;
	}

	function press(): void {
		if (body) void expand();
		else onOpen?.();
	}

	onMount(() => {
		const onKey = (event: KeyboardEvent) => event.key === 'Escape' && open && void collapse();
		window.addEventListener('keydown', onKey);
		return () => window.removeEventListener('keydown', onKey);
	});
</script>

{#snippet action(expanded: boolean)}
	<span class="flex size-[var(--space-touch)] shrink-0 items-center justify-center">
		<span class="flex size-[var(--size-control-small)] items-center justify-center rounded-full {bgColor[actionColor]}">
			<AppIcon icon={expanded ? 'Close' : 'ChevronRight'} tint={actionTint} size={20} />
		</span>
	</span>
{/snippet}

{#snippet header(expanded: boolean)}
	{#if centered}
		<div class="relative flex w-full items-center justify-center">
			<div class="w-full" use:dynamicStyle={{ 'padding-inline': 'var(--space-touch)' }}>{@render head(expanded)}</div>
			<div class="absolute top-1/2 right-0 -translate-y-1/2">{@render action(expanded)}</div>
		</div>
	{:else}
		<div class="flex w-full items-center gap-3">
			{@render leading?.()}
			<div class="min-w-0 flex-1">{@render head(expanded)}</div>
			{@render action(expanded)}
		</div>
	{/if}
{/snippet}

<div
	bind:this={card}
	role="button"
	tabindex="0"
	aria-label={openLabel}
	onclick={press}
	onkeydown={(event) => (event.key === 'Enter' || event.key === ' ') && press()}
	class="flex w-full cursor-pointer flex-col overflow-hidden rounded-card {fill ? 'h-full' : ''} {containerColor === 'transparent' ? '' : bgColor[containerColor]}"
	use:dynamicStyle={{ padding: padding, visibility: open ? 'hidden' : 'visible' }}
>
	<!-- Isi di tengah bila muat; bila lebih tinggi, rata atas dan bagian bawahnya terpotong, seperti Column di app. -->
	<div class="my-auto w-full">{@render header(false)}</div>
</div>

{#if open}
	<div
		use:portal
		class="fixed z-30 flex flex-col overflow-hidden {containerColor === 'transparent' ? 'bg-surface' : bgColor[containerColor]}"
		use:dynamicStyle={{ left: `${box.left}px`, top: `${box.top}px`, width: `${box.width}px`, height: `${box.height}px`, 'border-radius': `${radius}px` }}
	>
		<div class="flex w-full justify-center">
			<div class="w-full max-w-[var(--size-content-max)]" use:dynamicStyle={{ padding: '16px' }}>
				<button type="button" onclick={() => void collapse()} aria-label={closeLabel} class="block w-full text-start">{@render header(true)}</button>
			</div>
		</div>
		<div class="flex w-full min-h-0 flex-1 justify-center overflow-y-auto">
			<div class="flex w-full max-w-[var(--size-content-max)] flex-col gap-2 px-4 pb-4" use:dynamicStyle={{ opacity: bodyProgress, transform: `translateY(${(1 - bodyProgress) * RISE}px)` }}>
				{@render body?.()}
			</div>
		</div>
	</div>
{/if}
