<script lang="ts">
	import AppIcon from '$lib/components/icon/AppIcon.svelte';
	import type { IconName } from '$lib/theme/icons';

	/** Tombol sumber berkas dengan ikon besar di atas teks; `live` diambil saat itu juga dengan kamera, `library` dipilih dari berkas yang sudah ada. */
	let {
		label,
		icon,
		onclick,
		tone = 'live',
		enabled = true
	}: { label: string; icon: IconName; onclick: () => void; tone?: 'live' | 'library'; enabled?: boolean } = $props();
</script>

<button
	type="button"
	disabled={!enabled}
	{onclick}
	class="flex min-h-[var(--space-touch)] w-full flex-col items-center gap-1 rounded-card p-3 {tone === 'live' ? 'bg-primary text-on-primary' : 'bg-accent text-content'} {enabled ? '' : 'disabled-look'}"
>
	<AppIcon {icon} tint={tone === 'live' ? 'on-primary' : 'content'} size={40} />
	<span class="text-label text-center">{label}</span>
</button>
