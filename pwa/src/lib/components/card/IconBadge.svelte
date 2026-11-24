<script lang="ts">
	import AppIcon from '$lib/components/icon/AppIcon.svelte';
	import type { IconName } from '$lib/theme/icons';

	/** Ikon di dalam lingkaran berlatar muda, untuk penanda jenis pada baris daftar. */
	let { icon }: { icon: IconName } = $props();
</script>

<span class="flex size-[var(--space-compact)] shrink-0 items-center justify-center rounded-full bg-selected">
	<AppIcon {icon} tint="primary" size={20} />
</span>
