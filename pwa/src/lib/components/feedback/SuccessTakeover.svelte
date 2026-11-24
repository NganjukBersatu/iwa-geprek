<script lang="ts">
	import { dynamicStyle } from '$lib/platform/dynamic-style';
	import { onMount } from 'svelte';
	import AppIcon from '$lib/components/icon/AppIcon.svelte';
	import { animateValue } from '$lib/theme/animate';
	import { bgColor, textColor, type ColorToken } from '$lib/theme/colors';
	import { bounce, emphasized, exit, standard } from '$lib/theme/ease';

	const FLOOD_MILLIS = 650;
	const BADGE_MILLIS = 480;
	const CHECK_MILLIS = 420;
	const CHECK_DELAY_MILLIS = 220;
	const TEXT_MILLIS = 420;
	const TEXT_STAGGER_MILLIS = 90;
	const COUNT_MILLIS = 900;
	const TEXT_COUNT = 4;
	const TEXT_MUTE_ALPHA = 0.85;
	const BADGE_FILL_PERCENT = 20;
	const CHECK_START_SCALE = 0.4;
	const BADGE_SIZE = 100;
	const CHECK_SIZE = 56;
	const TEXT_RISE = 14;
	/** Tombol kirim berada 16 px di atas tepi bawah dengan tinggi 48 px, tempat banjir warna bermula. */
	const ORIGIN_LIFT = 16 + 24;

	/** Layar penuh yang dibanjiri warna dari tepi bawah tempat tombol kirim berada, lalu centang tergambar, teks naik berurutan, dan angka menghitung naik dari nol. */
	let {
		title,
		message,
		countTo,
		countLabel,
		actionLabel,
		containerColor,
		contentColor,
		onDone
	}: {
		title: string;
		message: string;
		countTo: number | null;
		countLabel: (value: number) => string;
		actionLabel: string;
		containerColor: ColorToken;
		contentColor: ColorToken;
		onDone: () => void;
	} = $props();

	let flood = $state(0);
	let badge = $state(0);
	let check = $state(0);
	let texts = $state<number[]>(Array.from({ length: TEXT_COUNT }, () => 0));
	let count = $state(0);
	let closed = false;
	let width = $state(390);
	let height = $state(800);
	let safeBottom = $state(0);
	let probe: HTMLDivElement | undefined = $state();

	const countEase = (progress: number) => 1 - (1 - progress) ** 3;

	onMount(() => {
		safeBottom = probe ? probe.offsetHeight : 0;
		void (async () => {
			await animateValue({ from: 0, to: 1, durationMillis: FLOOD_MILLIS, easing: exit, onUpdate: (value) => (flood = value) }).done;
			void animateValue({ from: 0, to: 1, durationMillis: BADGE_MILLIS, easing: bounce, onUpdate: (value) => (badge = value) });
			await animateValue({ from: 0, to: 1, durationMillis: CHECK_MILLIS, delayMillis: CHECK_DELAY_MILLIS, easing: standard, onUpdate: (value) => (check = value) }).done;
			texts.forEach((_, index) => {
				void animateValue({
					from: 0,
					to: 1,
					durationMillis: TEXT_MILLIS,
					delayMillis: index * TEXT_STAGGER_MILLIS,
					easing: emphasized,
					onUpdate: (value) => (texts[index] = value)
				});
			});
			await animateValue({ from: 0, to: 1, durationMillis: COUNT_MILLIS, easing: countEase, onUpdate: (value) => (count = value) }).done;
		})();
	});

	function close(): void {
		if (closed) return;
		closed = true;
		onDone();
	}

	const originX = $derived(width / 2);
	const originY = $derived(height - safeBottom - ORIGIN_LIFT);
	const radius = $derived(Math.hypot(Math.max(originX, width - originX), Math.max(originY, height - originY)));
	const rise = (progress: number) => ({ opacity: progress, transform: `translateY(${(1 - progress) * TEXT_RISE}px)` });
</script>

<svelte:window bind:innerWidth={width} bind:innerHeight={height} onkeydown={(event) => event.key === 'Escape' && close()} />

<div bind:this={probe} class="pointer-events-none fixed bottom-0 left-0 w-0" use:dynamicStyle={{ height: 'var(--safe-bottom)' }} aria-hidden="true"></div>

<div class="fixed inset-0 z-[60]" role="dialog" aria-modal="true" aria-label={title}>
	<div class="absolute inset-0 {bgColor[containerColor]}" use:dynamicStyle={{ 'clip-path': `circle(${radius * flood}px at ${originX}px ${originY}px)` }}></div>
	<div class="absolute inset-0 flex flex-col items-center justify-center gap-2 px-4 {textColor[contentColor]}">
		<div
			class="mb-2 flex items-center justify-center rounded-full"
			use:dynamicStyle={{ width: `${BADGE_SIZE}px`, height: `${BADGE_SIZE}px`, 'background-color': `color-mix(in srgb, currentColor ${BADGE_FILL_PERCENT}%, transparent)`, transform: `scale(${badge})` }}
		>
			<span use:dynamicStyle={{ opacity: check, transform: `scale(${CHECK_START_SCALE + (1 - CHECK_START_SCALE) * check})` }}>
				<AppIcon icon="Check" tint={contentColor} size={CHECK_SIZE} />
			</span>
		</div>
		<p class="text-title m-0 text-center" use:dynamicStyle={rise(texts[0] ?? 0)}>{title}</p>
		{#if countTo !== null}
			<p class="text-display m-0 text-center" use:dynamicStyle={rise(texts[1] ?? 0)}>{countLabel(Math.round(countTo * count))}</p>
		{/if}
		<p class="text-body m-0 text-center" use:dynamicStyle={{ ...rise(texts[2] ?? 0), color: `color-mix(in srgb, currentColor ${TEXT_MUTE_ALPHA * 100}%, transparent)` }}>{message}</p>
		<button
			type="button"
			onclick={close}
			class="text-button mt-6 w-full max-w-[var(--size-content-max)] rounded-full px-4 py-3 text-center {bgColor[contentColor]} {textColor[containerColor]}"
			use:dynamicStyle={rise(texts[3] ?? 0)}
		>
			{actionLabel}
		</button>
	</div>
</div>
