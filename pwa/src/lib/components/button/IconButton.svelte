<script lang="ts">
	import AppIcon from '$lib/components/icon/AppIcon.svelte';
	import { bgColor, textColor, type ColorToken } from '$lib/theme/colors';
	import type { IconName } from '$lib/theme/icons';

	/** Tombol satu ikon dengan target sentuh penuh, dengan [badge] (misalnya jumlah item) tampil pekat di sudut kanan atas bila diisi; [container] mengisi tombol menjadi lingkaran. */
	let {
		icon,
		label,
		onclick,
		tint = 'content',
		badge = null,
		container = null,
		badgeColor = 'primary',
		onBadgeColor = 'on-primary'
	}: {
		icon: IconName;
		label: string;
		onclick: () => void;
		tint?: ColorToken;
		badge?: string | null;
		container?: ColorToken | null;
		badgeColor?: ColorToken;
		onBadgeColor?: ColorToken;
	} = $props();
</script>

<button type="button" {onclick} aria-label={label} class="relative flex size-[var(--space-touch)] shrink-0 items-center justify-center rounded-full {container ? bgColor[container] : ''}">
	<AppIcon {icon} {tint} />
	{#if badge}
		<span class="text-label absolute -top-1 -right-1 rounded-full px-2 py-1 {bgColor[badgeColor]} {textColor[onBadgeColor]}">{badge}</span>
	{/if}
</button>
