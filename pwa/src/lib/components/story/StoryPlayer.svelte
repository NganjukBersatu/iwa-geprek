<script lang="ts">
	import { dynamicStyle } from '$lib/platform/dynamic-style';
	import AppIcon from '$lib/components/icon/AppIcon.svelte';
	import MarkdownContent from '$lib/components/markdown/MarkdownContent.svelte';
	import { STORY_TRANSITION_KINDS, storyIn, storyOut, type StoryPage } from './transitions';

	const SWIPE_THRESHOLD = 56;

	/** Pemutar halaman cerita dengan batang kemajuan, geser atau tombol untuk berpindah, peralihan berganti, dan halaman panjang bisa digulir. */
	let {
		pages,
		title,
		previousLabel,
		nextLabel,
		finishLabel,
		progressLabel,
		onFinish
	}: {
		pages: readonly StoryPage[];
		title?: string;
		previousLabel: string;
		nextLabel: string;
		finishLabel: string;
		progressLabel: (current: number, total: number) => string;
		onFinish: () => void;
	} = $props();

	let index = $state(0);
	let forward = $state(true);
	let startX = 0;

	const last = $derived(pages.length - 1);
	const kind = $derived(STORY_TRANSITION_KINDS[index % STORY_TRANSITION_KINDS.length] ?? 'push');
	const page = $derived(pages[index]);

	function previous(): void {
		if (index > 0) {
			forward = false;
			index -= 1;
		}
	}

	function next(): void {
		if (index < last) {
			forward = true;
			index += 1;
		} else {
			onFinish();
		}
	}

	function onPointerUp(event: PointerEvent): void {
		const travelled = event.clientX - startX;
		if (travelled <= -SWIPE_THRESHOLD) next();
		else if (travelled >= SWIPE_THRESHOLD) previous();
	}
</script>

<div class="flex size-full flex-col items-center gap-3" use:dynamicStyle={{ padding: '16px var(--page-padding)' }}>
	<div class="flex min-h-0 w-full max-w-[var(--size-content-max)] flex-1 flex-col gap-3">
		<div class="flex w-full gap-1">
			{#each pages as _, i (i)}
				<span class="h-1 flex-1 rounded-full {i <= index ? 'bg-primary' : 'bg-divider'}" use:dynamicStyle={{ transition: 'background-color var(--effect-standard)' }}></span>
			{/each}
		</div>
		{#if title}<p class="text-label m-0 text-content-muted">{title}</p>{/if}
		<div class="relative min-h-0 w-full flex-1 overflow-hidden" onpointerdown={(event) => (startX = event.clientX)} onpointerup={onPointerUp} role="presentation">
			{#key index}
				<div class="absolute inset-0 flex flex-col gap-3 overflow-y-auto rounded-card bg-surface p-4" in:storyIn={{ kind, forward }} out:storyOut={{ kind, forward }}>
					{#if page}
						<p class="text-headline m-0 text-content">{page.title}</p>
						<MarkdownContent source={page.body} />
					{/if}
				</div>
			{/key}
		</div>
		<div class="flex w-full items-center justify-between">
			<button type="button" onclick={previous} aria-label={previousLabel} class="flex size-[var(--space-touch)] items-center justify-center rounded-full">
				<AppIcon icon="ChevronLeft" tint={index > 0 ? 'content' : 'content-muted'} class={index > 0 ? '' : 'disabled-look'} />
			</button>
			<span class="text-label text-content-muted">{progressLabel(index + 1, pages.length)}</span>
			<button type="button" onclick={next} aria-label={index === last ? finishLabel : nextLabel} class="flex size-[var(--space-touch)] items-center justify-center rounded-full">
				<AppIcon icon={index === last ? 'Close' : 'ChevronRight'} tint="content" />
			</button>
		</div>
	</div>
</div>
