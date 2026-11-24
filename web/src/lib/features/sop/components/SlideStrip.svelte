<script lang="ts">
	import IconButton from '$lib/components/button/IconButton.svelte';
	import Button from '$lib/components/button/Button.svelte';
	import type { SopDraftState } from '../sop-draft.svelte';
	import { sopText } from '$lib/text/sop';
	import { format } from '$lib/text/format';

	let { draft }: { draft: SopDraftState } = $props();

</script>

<div class="flex flex-wrap items-center gap-2 border-b border-slate-100 p-3 tablet:px-5">
	<div role="tablist" aria-label={sopText.slide} class="flex min-w-0 flex-1 gap-1.5 overflow-x-auto py-1">
		{#each draft.slides as slide, index (slide.uid)}
			<button
				type="button"
				role="tab"
				aria-selected={index === draft.selected}
				title={slide.title || format(sopText.slideNumber, { number: index + 1 })}
				onclick={() => draft.select(index)}
				class="flex min-h-9 shrink-0 items-center gap-2 rounded-full border px-3 text-xs font-semibold transition-colors motion-reduce:transition-none {index === draft.selected ? 'border-brand bg-brand-soft text-brand' : 'border-slate-200 bg-white text-slate-600 hover:border-brand-line'}"
			>
				<span class="flex size-5 items-center justify-center rounded-full text-xs {index === draft.selected ? 'bg-brand text-white' : 'bg-slate-100 text-slate-500'}">{index + 1}</span>
				<span class="max-w-32 truncate">{slide.title || sopText.untitled}</span>
			</button>
		{/each}
	</div>
	<div class="flex shrink-0 items-center gap-0.5">
		<IconButton icon="arrow-left" label={sopText.moveSlideLeft} disabled={draft.selected === 0} onclick={() => draft.move(draft.selected, -1)} />
		<IconButton icon="arrow-right" label={sopText.moveSlideRight} disabled={draft.selected >= draft.slides.length - 1} onclick={() => draft.move(draft.selected, 1)} />
		<IconButton icon="trash" label={sopText.removeSlide} tone="danger" disabled={draft.slides.length <= 1} onclick={() => draft.remove(draft.selected)} />
		<Button label={sopText.addSlide} icon="plus" variant="tertiary" small compact onclick={() => draft.add()} />
	</div>
</div>
