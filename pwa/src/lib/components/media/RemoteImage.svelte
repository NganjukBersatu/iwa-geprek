<script lang="ts">
	import { dynamicStyle } from '$lib/platform/dynamic-style';
	/** Gambar dari alamat jaringan dengan bingkai berrasio 3 : 4 dan gambar dipotong mengisi bingkai; dengan [fit], gambar tampil utuh selebar tempatnya. */
	let { url, description, fit = false }: { url: string; description: string | null; fit?: boolean } = $props();
</script>

{#if fit}
	<img src={url} alt={description ?? ''} class="w-full rounded-field bg-selected" />
{:else}
	<div class="w-full overflow-hidden rounded-field bg-selected" use:dynamicStyle={{ 'aspect-ratio': '3 / 4' }}>
		<img src={url} alt={description ?? ''} class="size-full object-cover" />
	</div>
{/if}
