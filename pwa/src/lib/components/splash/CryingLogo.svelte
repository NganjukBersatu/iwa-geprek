<script lang="ts">
	import { dynamicStyle } from '$lib/platform/dynamic-style';
	import AppIcon from '$lib/components/icon/AppIcon.svelte';
	import type { IconName } from '$lib/theme/icons';

	const SWAY_MILLIS = 2600;
	const DROOP_DISTANCE = 5;
	const TILT_DEGREES = 2;
	const TEAR_MILLIS = 1800;
	const TEAR_OFFSET_MILLIS = 900;
	/** Letak air mata pada logo 1024 x 1024, diukur dari pikselnya. */
	const TEAR_COLUMNS = [448, 578];
	const TEAR_START_Y = 528;
	const TEAR_TRAVEL = 574 - 528;
	const TEAR_RADIUS = 11;
	const TEAR_ALPHA = 0.8;
	const BADGE_SCALE = 0.28;
	const BADGE_ICON_SCALE = 0.17;

	/** Logo kafe yang menangis: air mata jatuh dari bawah kacamatanya dan badannya terkulai pelan, dengan lencana di pojok kanan bawah. */
	let { badgeIcon, size = 176 }: { badgeIcon: IconName; size?: number } = $props();

	function teardrop(centerX: number): string {
		const r = TEAR_RADIUS;
		const cy = TEAR_START_Y;
		const top = cy - r * 2;
		return [
			`M${centerX} ${top}`,
			`C${centerX + r * 0.3} ${top + r * 0.8} ${centerX + r} ${cy - r * 0.8} ${centerX + r} ${cy}`,
			`C${centerX + r} ${cy + r * 0.55} ${centerX + r * 0.55} ${cy + r} ${centerX} ${cy + r}`,
			`C${centerX - r * 0.55} ${cy + r} ${centerX - r} ${cy + r * 0.55} ${centerX - r} ${cy}`,
			`C${centerX - r} ${cy - r * 0.8} ${centerX - r * 0.3} ${top + r * 0.8} ${centerX} ${top}`,
			'Z'
		].join(' ');
	}
</script>

<div class="relative shrink-0" use:dynamicStyle={{ width: `${size}px`, height: `${size}px` }}>
	<div class="crying-body size-full">
		<img src="/brand-logo.png" alt="" class="size-full" />
		<svg viewBox="0 0 1024 1024" class="absolute inset-0 size-full" aria-hidden="true">
			{#each TEAR_COLUMNS as column, index (column)}
				<path class="crying-tear fill-info" d={teardrop(column)} use:dynamicStyle={{ 'animation-delay': `${index * TEAR_OFFSET_MILLIS}ms` }} />
			{/each}
		</svg>
	</div>
	<span
		class="absolute right-0 bottom-0 flex items-center justify-center rounded-full bg-accent"
		use:dynamicStyle={{ width: `${size * BADGE_SCALE}px`, height: `${size * BADGE_SCALE}px` }}
	>
		<AppIcon icon={badgeIcon} tint="content" size={size * BADGE_ICON_SCALE} />
	</span>
</div>

<style>
	.crying-body {
		animation: crying-sway 2600ms var(--ease-standard) infinite alternate;
	}
	.crying-tear {
		opacity: 0;
		animation: crying-tear 1800ms linear infinite;
	}
	@keyframes crying-sway {
		from {
			transform: translateY(0) rotate(-2deg);
		}
		to {
			transform: translateY(5px) rotate(2deg);
		}
	}
	@keyframes crying-tear {
		0% {
			opacity: 0;
			transform: translateY(0);
		}
		15% {
			opacity: 0.8;
		}
		70% {
			opacity: 0.8;
		}
		100% {
			opacity: 0;
			transform: translateY(46px);
		}
	}
</style>
