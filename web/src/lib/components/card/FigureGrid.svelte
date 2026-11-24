<script lang="ts">
	/** A few figures side by side inside a card: the label small above, the value below. */
	let { figures, label }: { figures: { label: string; value: string }[]; label: string } = $props();
</script>

<dl class="grid gap-x-6 gap-y-3 sm:grid-cols-2 laptop:grid-cols-4" aria-label={label}>
	{#each figures as figure (figure.label)}
		<div class="min-w-0">
			<dt class="text-xs font-medium text-slate-500">{figure.label}</dt>
			<dd class="mt-0.5 text-sm font-semibold text-slate-800 wrap-anywhere">{figure.value}</dd>
		</div>
	{/each}
</dl>
