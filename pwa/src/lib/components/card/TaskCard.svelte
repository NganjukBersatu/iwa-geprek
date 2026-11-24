<script lang="ts">
	import PrimaryButton from '$lib/components/button/PrimaryButton.svelte';
	import StatusBadge from '$lib/components/feedback/StatusBadge.svelte';
	import type { BadgeTone } from '$lib/components/feedback/types';
	import AppIcon from '$lib/components/icon/AppIcon.svelte';
	import type { ColorToken } from '$lib/theme/colors';
	import type { IconName } from '$lib/theme/icons';

	type Tone = 'light' | 'green' | 'tan';
	type Look = { fill: string; ring: string; onRing: ColorToken; check: string; onFill: string; onFillMuted: string; button: ColorToken; onButton: ColorToken };

	/** Satu kartu untuk ketiga jenis tugas: putih selama belum selesai, berwarna jenisnya setelah selesai; [tone] light = tugas karyawan, green = tugas rutin, tan = tugas outlet. */
	let {
		title,
		caption = null,
		completed,
		tone,
		icon,
		badge = null,
		actionLabel = null,
		onAction,
		onclick
	}: {
		title: string;
		caption?: string | null;
		completed: boolean;
		tone: Tone;
		icon: IconName;
		badge?: { text: string; tone: BadgeTone } | null;
		/** Tombol di bawah kartu; tanpa label berarti tanpa tombol. Di kartu selesai tombolnya berlatar putih supaya terbaca di atas warna jenis. */
		actionLabel?: string | null;
		onAction?: () => void;
		/** Ketuk kartu, misalnya membuka rincian; tanpa ini kartu bukan tombol. */
		onclick?: () => void;
	} = $props();

	const looks: Record<Tone, Look> = {
		light: { fill: 'bg-selected', ring: 'bg-selected', onRing: 'primary', check: 'bg-primary', onFill: 'text-primary', onFillMuted: 'text-content-muted', button: 'selected', onButton: 'primary' },
		green: { fill: 'bg-primary', ring: 'bg-primary', onRing: 'on-primary', check: 'bg-on-primary-subtle', onFill: 'text-on-primary', onFillMuted: 'text-on-primary-muted', button: 'primary', onButton: 'on-primary' },
		tan: { fill: 'bg-accent', ring: 'bg-accent', onRing: 'content', check: 'bg-primary', onFill: 'text-content', onFillMuted: 'text-content', button: 'accent', onButton: 'content' }
	};
	const look = $derived(looks[tone]);
</script>

{#snippet summary()}
	<span class="flex size-[var(--space-compact)] shrink-0 items-center justify-center rounded-full {completed ? look.check : look.ring}">
		<AppIcon icon={completed ? 'Check' : icon} tint={completed ? 'on-primary' : look.onRing} size={20} />
	</span>
	<span class="min-w-0 flex-1 text-left">
		<span class="text-title block truncate {completed ? look.onFill : 'text-content'}">{title}</span>
		{#if caption}<span class="text-caption block truncate {completed ? look.onFillMuted : 'text-content-muted'}">{caption}</span>{/if}
	</span>
	{#if badge && !completed}<StatusBadge text={badge.text} tone={badge.tone} />{/if}
{/snippet}

<div class="flex w-full flex-col gap-3 rounded-card p-4 {completed ? look.fill : 'border border-divider bg-surface'}">
	{#if onclick}
		<button type="button" class="flex w-full items-center gap-3" {onclick}>{@render summary()}</button>
	{:else}
		<div class="flex w-full items-center gap-3">{@render summary()}</div>
	{/if}
	{#if actionLabel && onAction}
		{#if completed}
			<PrimaryButton text={actionLabel} onclick={onAction} container="surface" content={tone === 'tan' ? 'content' : 'primary'} />
		{:else}
			<PrimaryButton text={actionLabel} onclick={onAction} container={look.button} content={look.onButton} />
		{/if}
	{/if}
</div>
