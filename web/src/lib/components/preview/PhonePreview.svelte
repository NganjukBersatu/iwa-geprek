<script lang="ts">
	import { sopText } from '$lib/text/sop';
	import MarkdownView from '../markdown/MarkdownView.svelte';
	import { controlText } from '$lib/text/controls';

	type Page = { title: string; body: string };

	let {
		title,
		pages,
		index = $bindable(0),
		caption = controlText.employeePreview
	}: {
		title: string;
		pages: Page[];
		index?: number;
		caption?: string;
	} = $props();

	const last = $derived(Math.max(0, pages.length - 1));
	const current = $derived(Math.min(index, last));
	const page = $derived(pages[current]);
</script>

<figure class="mx-auto flex w-full max-w-[22rem] flex-col gap-2">
	<figcaption class="text-center text-xs font-semibold text-slate-500">{caption}</figcaption>
	<div class="rounded-[2.25rem] border-[6px] border-slate-800 bg-slate-800 shadow-lg">
		<div class="flex h-[40rem] flex-col overflow-hidden rounded-[1.75rem] bg-brand-page">
			<div class="flex gap-1 px-4 pt-4" aria-hidden="true">
				{#each pages as _, at (at)}
					<span class="h-1 flex-1 rounded-full transition-colors duration-300 motion-reduce:transition-none {at <= current ? 'bg-brand-accent-deep' : 'bg-slate-200'}"></span>
				{/each}
			</div>
			<p class="truncate px-4 pt-2 text-xs font-semibold text-slate-500">{title || sopText.sopTitle}</p>
			<div class="min-h-0 flex-1 p-3">
				<div class="h-full overflow-y-auto rounded-2xl bg-white p-4">
					{#if page}
						<h3 class="mb-3 text-lg font-semibold text-slate-800">{page.title || sopText.slideTitle}</h3>
						<MarkdownView source={page.body} />
					{:else}
						<p class="text-sm text-slate-500">{controlText.noSlides}</p>
					{/if}
				</div>
			</div>
			<div class="flex items-center justify-between px-4 pb-4">
				<button
					type="button"
					onclick={() => (index = Math.max(0, current - 1))}
					disabled={current === 0}
					aria-label={controlText.previousSlide}
					class="flex size-10 min-h-0 min-w-0 items-center justify-center rounded-full text-slate-700 hover:bg-white disabled:opacity-30 disabled:hover:bg-transparent"
				>
					<i class="ti ti-chevron-left text-xl" aria-hidden="true"></i>
				</button>
				<span class="text-xs font-semibold text-slate-500" aria-live="polite">{pages.length === 0 ? '0/0' : `${current + 1}/${pages.length}`}</span>
				<button
					type="button"
					onclick={() => (index = Math.min(last, current + 1))}
					disabled={current === last}
					aria-label={controlText.nextSlide}
					class="flex size-10 min-h-0 min-w-0 items-center justify-center rounded-full text-slate-700 hover:bg-white disabled:opacity-30 disabled:hover:bg-transparent"
				>
					<i class="ti ti-chevron-right text-xl" aria-hidden="true"></i>
				</button>
			</div>
		</div>
	</div>
</figure>
