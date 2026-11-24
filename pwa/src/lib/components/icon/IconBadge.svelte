<script lang="ts">
	import type { IconName } from '$lib/theme/icons';
	import AppIcon from './AppIcon.svelte';

	/** Ikon di dalam lingkaran berlatar muda, untuk penanda jenis pada baris daftar (IconBadge app). */
	let { icon }: { icon: IconName } = $props();
</script>

<span class="flex size-[var(--space-compact)] shrink-0 items-center justify-center rounded-full bg-selected">
	<AppIcon {icon} tint="primary" size={20} />
</span>
