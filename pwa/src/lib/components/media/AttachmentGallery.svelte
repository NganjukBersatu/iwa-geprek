<script lang="ts">
	import AppIcon from '$lib/components/icon/AppIcon.svelte';
	import ImagePreview from './ImagePreview.svelte';
	import MediaTile from './MediaTile.svelte';
	import type { RemoteAttachment } from './types';

	/** Deretan lampiran: foto dibuka dengan pratinjau layar penuh, video dibuka di pemutar perangkat, dan tombol hapus tampil bila [onRemove] diberikan. */
	let { attachments, onRemove }: { attachments: readonly RemoteAttachment[]; onRemove?: (attachment: RemoteAttachment) => void } = $props();

	let previewUrl = $state<string | null>(null);
</script>

{#if attachments.length > 0}
	<div class="flex flex-wrap gap-2">
		{#each attachments as item (item.id)}
			<MediaTile
				onclick={() => (item.isVideo ? window.open(item.url, '_blank', 'noopener') : (previewUrl = item.url))}
				onRemove={onRemove && item.removable ? () => onRemove(item) : undefined}
			>
				{#if item.isVideo}
					<AppIcon icon="Video" tint="primary" size={28} />
				{:else}
					<img src={item.url} alt="" class="absolute inset-0 size-full object-cover" />
				{/if}
			</MediaTile>
		{/each}
	</div>
	{#if previewUrl}<ImagePreview url={previewUrl} onDismiss={() => (previewUrl = null)} />{/if}
{/if}
