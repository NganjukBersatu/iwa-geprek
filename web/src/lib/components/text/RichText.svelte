<script lang="ts">
	import { format } from '$lib/text/format';

	/** A sentence with values and emphasis from one template: {name} takes a value, **text** is strong, and __text__ is bold. */
	let { template, values = {} }: { template: string; values?: Record<string, string | number> } = $props();

	type Mark = 'strong' | 'bold' | null;
	const MARKS = /(\*\*|__)/;

	// The marks are read before the values are put in, so a value that holds ** or __ is shown as typed and never emphasises anything.
	const pieces = $derived.by(() => {
		const found: { text: string; mark: Mark }[] = [];
		let mark: Mark = null;
		for (const part of template.split(MARKS)) {
			if (part === '**') mark = mark === 'strong' ? null : 'strong';
			else if (part === '__') mark = mark === 'bold' ? null : 'bold';
			else if (part) found.push({ text: format(part, values), mark });
		}
		return found;
	});
</script>

{#each pieces as piece, index (index)}{#if piece.mark === 'strong'}<strong class="text-slate-800">{piece.text}</strong>{:else if piece.mark === 'bold'}<b>{piece.text}</b>{:else}{piece.text}{/if}{/each}
