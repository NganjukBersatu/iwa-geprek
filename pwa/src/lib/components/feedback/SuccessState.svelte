<script lang="ts">
	import IconBadge from '$lib/components/card/IconBadge.svelte';
	import type { IconName } from '$lib/theme/icons';

	/** Keadaan berhasil: ikon, judul, dan satu kalimat keterangan di tengah. */
	let { title, message, icon, class: className = '' }: { title: string; message: string; icon: IconName; class?: string } = $props();
</script>

<div class="flex w-full flex-col items-center gap-3 py-6 {className}">
	<IconBadge {icon} />
	<p class="text-title m-0 text-center text-content">{title}</p>
	<p class="text-body m-0 text-center text-content-muted">{message}</p>
</div>
