<script lang="ts">
	import CodeBadge from './CodeBadge.svelte';
	import ListRow from './ListRow.svelte';
	import StatusBadge from '$lib/components/feedback/StatusBadge.svelte';

	/** Baris satu penugasan shift: judul, keterangan, lencana kode berwarna, dan penanda opsional. */
	let {
		title,
		detail,
		caption,
		footnote,
		code,
		codeColor = null,
		tag
	}: {
		title: string;
		detail?: string | null;
		caption?: string | null;
		footnote?: string | null;
		code?: string | null;
		codeColor?: string | null;
		tag?: string | null;
	} = $props();
</script>

<ListRow {title} {detail} {caption} {footnote}>
	{#snippet trailing()}
		{#if tag || code}
			<span class="flex items-center gap-2">
				{#if tag}<StatusBadge text={tag} tone="positive" />{/if}
				{#if code}<CodeBadge text={code} color={codeColor} />{/if}
			</span>
		{/if}
	{/snippet}
</ListRow>
