<script lang="ts">
	import ImagePreview from './ImagePreview.svelte';
	import RemoteImage from './RemoteImage.svelte';
	import type { PhotoItem } from './types';

	/** Dua foto bersebelahan dengan keterangan dan pratinjau layar penuh saat diketuk; yang kosong menyisakan ruangnya dan keduanya kosong tidak tampil. */
	let { first, second }: { first: PhotoItem; second: PhotoItem } = $props();

	let previewUrl = $state<string | null>(null);
</script>

{#if first.url || second.url}
	<div class="flex w-full gap-3">
		{#each [first, second] as item, index (index)}
			{#if item.url}
				{@const url = item.url}
				<button type="button" onclick={() => (previewUrl = url)} class="flex min-w-0 flex-1 flex-col gap-1 text-start">
					<RemoteImage {url} description={item.caption} />
					<span class="text-caption text-content-muted">{item.caption}</span>
				</button>
			{:else}
				<span class="flex-1"></span>
			{/if}
		{/each}
	</div>
	{#if previewUrl}<ImagePreview url={previewUrl} onDismiss={() => (previewUrl = null)} />{/if}
{/if}
