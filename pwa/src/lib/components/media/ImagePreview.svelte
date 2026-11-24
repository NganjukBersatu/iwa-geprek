<script lang="ts">
	import { t } from '$lib/text/t';

	/** Pratinjau gambar layar penuh tanpa dipotong; ketuk di mana saja untuk menutup. */
	let { url, onDismiss }: { url: string; onDismiss: () => void } = $props();
</script>

<svelte:window onkeydown={(event) => event.key === 'Escape' && onDismiss()} />

<button type="button" onclick={onDismiss} class="fixed inset-0 z-50 flex items-center justify-center bg-scrim" aria-label={t('image_preview_close')}>
	<img src={url} alt={t('image_preview_close')} class="size-full object-contain" />
</button>
