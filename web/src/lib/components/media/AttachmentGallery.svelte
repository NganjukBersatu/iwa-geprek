<script lang="ts">
	import { controlText } from '$lib/text/controls';

	type Attachment = { id: string; kind: string; url: string; removable: boolean };

	let {
		attachments,
		alt,
		onremove,
		disabled = false
	}: {
		attachments: Attachment[];
		alt: string;
		/** Left out, nothing can be removed. */
		onremove?: (attachment: Attachment) => void;
		disabled?: boolean;
	} = $props();
</script>

<ul class="flex flex-wrap gap-2" aria-label={controlText.attachments}>
	{#each attachments as attachment (attachment.id)}
		<li class="relative overflow-hidden rounded-lg border border-slate-200 bg-slate-50">
			{#if attachment.kind === 'video'}
				<!-- svelte-ignore a11y_media_has_caption -->
				<video src={attachment.url} controls preload="metadata" class="h-32 max-w-full"></video>
			{:else}
				<a href={attachment.url} target="_blank" rel="noopener" aria-label={controlText.openPhoto}>
					<img src={attachment.url} {alt} class="h-32 w-auto object-cover" />
				</a>
			{/if}
			{#if onremove && attachment.removable}
				<button
					type="button"
					{disabled}
					aria-label={controlText.discardAttachment}
					onclick={() => onremove(attachment)}
					class="absolute right-1 top-1 flex size-6 items-center justify-center rounded-full bg-slate-800/70 text-white hover:bg-slate-800 disabled:opacity-50"
				>
					<i class="ti ti-x text-xs" aria-hidden="true"></i>
				</button>
			{/if}
		</li>
	{/each}
</ul>
