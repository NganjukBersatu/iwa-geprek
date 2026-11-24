<script lang="ts">
	import AppIcon from '$lib/components/icon/AppIcon.svelte';
	import { t } from '$lib/text/t';

	/** Tombol kembali berikon panah kiri dengan area ketuk penuh; dipakai di semua halaman turunan. */
	let { onclick }: { onclick: () => void } = $props();
</script>

<button type="button" {onclick} aria-label={t('common_back')} class="flex size-[var(--space-touch)] items-center justify-center rounded-full">
	<AppIcon icon="ChevronLeft" tint="primary" size={28} />
</button>
