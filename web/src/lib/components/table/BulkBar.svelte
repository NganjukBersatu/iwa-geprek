<script lang="ts">
	import Button from '../button/Button.svelte';
	import type { Action } from '../button/types';
	import type { Selection } from './selection.svelte';
	import { controlText } from '$lib/text/controls';
	import { format } from '$lib/text/format';

	let { selection, actions }: { selection: Selection; actions: Action[] } = $props();
</script>

{#if selection.count > 0}
	<div class="sticky bottom-3 z-20 flex flex-wrap items-center justify-between gap-2 rounded-xl border border-brand-line bg-white px-4 py-2.5 shadow-lg" role="region" aria-label={controlText.selectedRowActions}>
		<p class="text-sm font-semibold text-slate-700">{format(controlText.selectedCount, { count: selection.count })}</p>
		<div class="flex flex-wrap items-center gap-2">
			{#each actions as action (action.label)}
				<Button label={action.label} icon={action.icon} variant={action.danger ? 'danger' : 'secondary'} disabled={action.disabled} onclick={action.onclick} />
			{/each}
			<Button label={controlText.done} icon="x" onclick={() => selection.stop()} />
		</div>
	</div>
{/if}
