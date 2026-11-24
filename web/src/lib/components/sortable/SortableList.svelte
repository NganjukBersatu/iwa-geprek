<script lang="ts" generics="T">
	import type { Snippet } from 'svelte';
	import { reorder } from '$lib/motion/transitions';
	import { controlText } from '$lib/text/controls';
	import { format } from '$lib/text/format';

	let {
		items = $bindable([]),
		key,
		label,
		row
	}: {
		/** Reordered in place; the caller saves the new order when it is ready. */
		items?: T[];
		key: (item: T) => string;
		/** Names a row for screen readers and the move buttons. */
		label: (item: T) => string;
		row: Snippet<[T, number]>;
	} = $props();

	let dragging = $state<number | null>(null);
	let over = $state<number | null>(null);

	function move(from: number, to: number): void {
		if (from === to || to < 0 || to >= items.length) return;
		const copy = [...items];
		const [moved] = copy.splice(from, 1);
		copy.splice(to, 0, moved as T);
		items = copy;
	}

	function drop(index: number): void {
		if (dragging !== null) move(dragging, index);
		dragging = null;
		over = null;
	}

	const control = 'flex size-9 min-h-0 min-w-0 items-center justify-center rounded-lg text-slate-500 hover:bg-brand-soft hover:text-brand disabled:opacity-30 disabled:hover:bg-transparent';
</script>

<ol class="flex flex-col divide-y divide-slate-100" aria-label={controlText.dragToReorder}>
	{#each items as item, index (key(item))}
		<li
			animate:reorder
			draggable="true"
			ondragstart={() => (dragging = index)}
			ondragover={(event) => {
				event.preventDefault();
				over = index;
			}}
			ondragleave={() => (over = over === index ? null : over)}
			ondrop={(event) => {
				event.preventDefault();
				drop(index);
			}}
			ondragend={() => {
				dragging = null;
				over = null;
			}}
			class="flex items-center gap-3 px-4 py-2 tablet:px-5 {dragging === index ? 'opacity-50' : ''} {over === index && dragging !== index ? 'bg-brand-page' : 'bg-white'}"
		>
			<i class="ti ti-grip-vertical cursor-grab text-xl text-slate-500" aria-hidden="true"></i>
			<span class="w-6 text-right text-xs font-semibold tabular-nums text-slate-500">{index + 1}</span>
			<div class="min-w-0 flex-1">{@render row(item, index)}</div>
			<div class="flex shrink-0 items-center gap-0.5">
				<button type="button" class={control} disabled={index === 0} onclick={() => move(index, index - 1)} aria-label={format(controlText.moveUpName, { name: label(item) })}><i class="ti ti-arrow-up" aria-hidden="true"></i></button>
				<button type="button" class={control} disabled={index === items.length - 1} onclick={() => move(index, index + 1)} aria-label={format(controlText.moveDownName, { name: label(item) })}><i class="ti ti-arrow-down" aria-hidden="true"></i></button>
			</div>
		</li>
	{/each}
</ol>
