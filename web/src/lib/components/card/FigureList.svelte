<script lang="ts">
	/** total sums the rows above it; good and bad colour a result that can land either way. */
	type FigureEmphasis = 'total' | 'good' | 'bad';
	type Figure = { label: string; value: string; note?: string; emphasis?: FigureEmphasis };

	/** empty is shown in place of the list when there is no figure. */
	let { title, figures, empty }: { title?: string; figures: Figure[]; empty?: string } = $props();

	const INK: Record<FigureEmphasis, string> = {
		total: 'font-semibold text-slate-800',
		good: 'font-semibold text-success-700',
		bad: 'font-semibold text-danger-700'
	};
</script>

<section class="flex min-w-0 flex-col gap-1.5">
	{#if title}<h3 class="text-sm font-semibold text-slate-800">{title}</h3>{/if}
	{#if figures.length === 0 && empty}
		<p class="text-xs text-slate-500">{empty}</p>
	{:else}
		<dl class="grid grid-cols-[1fr_auto] gap-x-3 gap-y-1.5 text-xs">
			{#each figures as figure (figure.label)}
				{@const ink = figure.emphasis ? INK[figure.emphasis] : ''}
				{@const rule = figure.emphasis ? 'border-t border-slate-200 pt-1.5' : ''}
				<dt class="{rule} {ink || 'text-slate-500'}">
					{figure.label}
					{#if figure.note}<span class="block font-normal text-slate-500">{figure.note}</span>{/if}
				</dt>
				<dd class="{rule} text-right {ink || 'font-semibold text-slate-700'}">{figure.value}</dd>
			{/each}
		</dl>
	{/if}
</section>
