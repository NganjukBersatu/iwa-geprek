<script lang="ts">
	import Card from './Card.svelte';

	/** A row of cards, one figure each: the label small above, the value large below. */
	let { figures, label }: { figures: { label: string; value: string }[]; label: string } = $props();
</script>

<section class="grid gap-3 tablet:grid-cols-2 tablet:gap-4 laptop:grid-cols-4" aria-label={label}>
	{#each figures as figure (figure.label)}
		<Card class="flex flex-col gap-1">
			<span class="text-xs font-medium text-slate-500">{figure.label}</span>
			<span class="text-xl font-semibold text-slate-800 wrap-anywhere">{figure.value}</span>
		</Card>
	{/each}
</section>
