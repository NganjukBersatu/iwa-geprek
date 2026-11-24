<script lang="ts">
	import { dynamicStyle } from '$lib/platform/dynamic-style';
	import type { Snippet } from 'svelte';
	import { onMount } from 'svelte';
	import { animateValue, sleep } from '$lib/theme/animate';
	import { bounce, exit as exitCurve, standard } from '$lib/theme/ease';
	import { t } from '$lib/text/t';

	const LOGO_WIDTH_FRACTION = 0.4;
	const LOGO_HEIGHT_FRACTION = 0.35;
	const LOGO_ROTATE_FROM_DEGREES = -25;
	const START_DELAY_MILLIS = 250;
	const LOGO_MILLIS = 750;
	const NAME_MILLIS = 450;
	const HOLD_MILLIS = 1300;
	const EXIT_MILLIS = 850;
	const EXIT_OVERSHOOT = 1.02;
	const CONTENT_SCALE_FROM = 1.1;
	const CONTENT_DIM_FROM = 0.3;
	const NAME_RISE = 12;
	const EXIT_CORNER_RADIUS = 60;
	const SIDE_PANEL_WIDTH = 360;

	/** Layar pembuka: logo memantul masuk, nama naik, lalu layar terangkat membuka [children], yang baru disusun saat [ready] benar. */
	let { ready, children }: { ready: boolean; children: Snippet } = $props();

	let logo = $state(0);
	let name = $state(0);
	let exit = $state(0);
	let introDone = $state(false);
	let finished = $state(false);
	let started = false;
	let width = $state(390);
	let height = $state(800);

	onMount(() => {
		void (async () => {
			await sleep(START_DELAY_MILLIS);
			await animateValue({ from: 0, to: 1, durationMillis: LOGO_MILLIS, easing: bounce, onUpdate: (value) => (logo = value) }).done;
			await animateValue({ from: 0, to: 1, durationMillis: NAME_MILLIS, easing: standard, onUpdate: (value) => (name = value) }).done;
			await sleep(HOLD_MILLIS);
			introDone = true;
		})();
	});

	$effect(() => {
		if (!ready || !introDone || started) return;
		started = true;
		void animateValue({ from: 0, to: 1, durationMillis: EXIT_MILLIS, easing: exitCurve, onUpdate: (value) => (exit = value) }).done.then(() => (finished = true));
	});

	const logoSize = $derived(Math.min(width * LOGO_WIDTH_FRACTION, height * LOGO_HEIGHT_FRACTION, SIDE_PANEL_WIDTH));
	const contentScale = $derived(CONTENT_SCALE_FROM - (CONTENT_SCALE_FROM - 1) * exit);
</script>

<svelte:window bind:innerWidth={width} bind:innerHeight={height} />

<div class="fixed inset-0 overflow-hidden bg-background">
	{#if ready}
		<div class="h-full w-full" use:dynamicStyle={{ transform: finished ? 'none' : `scale(${contentScale})` }}>
			{@render children()}
		</div>
		{#if !finished}
			<div class="pointer-events-none absolute inset-0 bg-scrim" use:dynamicStyle={{ opacity: CONTENT_DIM_FROM * (1 - exit) }}></div>
		{/if}
	{/if}

	{#if !finished}
		<div
			class="absolute inset-0 flex items-center justify-center bg-background"
			role="status"
			aria-live="polite"
			aria-label={t('common_loading')}
			use:dynamicStyle={{ transform: `translateY(${-height * EXIT_OVERSHOOT * exit}px)`, 'border-bottom-left-radius': `${EXIT_CORNER_RADIUS * exit}px`, 'border-bottom-right-radius': `${EXIT_CORNER_RADIUS * exit}px` }}
		>
			<div class="flex w-full flex-col items-center gap-4 px-6">
				<img
					src="/brand-logo.png"
					alt=""
					use:dynamicStyle={{ width: `${logoSize}px`, height: `${logoSize}px`, transform: `scale(${logo}) rotate(${LOGO_ROTATE_FROM_DEGREES * (1 - logo)}deg)` }}
				/>
				<p class="text-headline m-0 text-center text-content" use:dynamicStyle={{ opacity: name, transform: `translateY(${NAME_RISE * (1 - name)}px)` }}>
					{t('splash_app_name')}
				</p>
			</div>
		</div>
	{/if}
</div>
