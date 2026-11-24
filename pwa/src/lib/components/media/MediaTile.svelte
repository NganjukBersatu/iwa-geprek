<script lang="ts">
	import type { Snippet } from 'svelte';
	import AppIcon from '$lib/components/icon/AppIcon.svelte';
	import { t } from '$lib/text/t';

	/** Kotak pratinjau satu lampiran: [onclick] membukanya dan tombol hapus di sudut tampil bila [onRemove] diberikan. */
	let { onclick, onRemove, removeEnabled = true, children }: { onclick?: () => void; onRemove?: () => void; removeEnabled?: boolean; children: Snippet } = $props();
</script>

<div class="relative flex size-[var(--size-thumbnail)] items-center justify-center overflow-hidden rounded-field border border-divider bg-selected">
	{#if onclick}
		<button type="button" {onclick} class="absolute inset-0 flex items-center justify-center">{@render children()}</button>
	{:else}
		{@render children()}
	{/if}
	{#if onRemove}
		<button
			type="button"
			disabled={!removeEnabled}
			onclick={onRemove}
			aria-label={t('media_remove')}
			class="absolute top-1 right-1 flex size-[var(--size-control-small)] items-center justify-center rounded-full bg-primary"
		>
			<AppIcon icon="Close" tint="on-primary" size={20} />
		</button>
	{/if}
</div>
