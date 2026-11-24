<script lang="ts">
	import AppIcon from '$lib/components/icon/AppIcon.svelte';
	import type { IconName } from '$lib/theme/icons';

	/** Kolom isian yang tampil seperti kolom teks tetapi berisi pilihan: ketukannya membuka pemilih, dan [icon] menandai jenisnya. */
	let { label, valueText, icon, onclick, enabled = true }: { label: string; valueText: string; icon: IconName; onclick: () => void; enabled?: boolean } = $props();
</script>

<div class="flex w-full flex-col gap-1">
	<span class="text-label text-content">{label}</span>
	<button
		type="button"
		disabled={!enabled}
		{onclick}
		class="flex min-h-[var(--space-touch)] w-full items-center gap-2 rounded-field border-[1.5px] border-outline bg-surface px-3"
	>
		<span class="text-body min-w-0 flex-1 text-start text-content">{valueText}</span>
		<AppIcon {icon} tint="primary" />
	</button>
</div>
