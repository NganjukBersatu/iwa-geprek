<script lang="ts">
	import { dynamicStyle } from '$lib/platform/dynamic-style';
	import AppIcon from '$lib/components/icon/AppIcon.svelte';
	import type { IconName } from '$lib/theme/icons';

	/** Tombol aksi utama berbentuk pil yang melayang di atas isi layar, berisi ikon dan label; letakkan di pojok bawah. */
	let { icon, label, onclick }: { icon: IconName; label: string; onclick: () => void } = $props();
</script>

<button type="button" {onclick} class="flex min-h-[var(--space-touch)] items-center gap-2 rounded-full bg-primary px-4" use:dynamicStyle={{ 'box-shadow': '0 3px 6px rgb(0 0 0 / 0.25)' }}>
	<AppIcon {icon} tint="on-primary" size={20} />
	<span class="text-label text-on-primary">{label}</span>
</button>
