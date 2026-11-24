<script lang="ts">
	import { format } from '$lib/text/format';
	import type { BulkResult } from '$lib/api/types';
	import { summarize } from '$lib/components/table/bulk';
	import Button from '../button/Button.svelte';
	import SuccessMark from '../motion/SuccessMark.svelte';
	import Modal from './Modal.svelte';
	import { actionText } from '$lib/text/actions';
	import { controlText } from '$lib/text/controls';

	let {
		result,
		names,
		verb,
		onclose
	}: {
		result: BulkResult | null;
		names: string[];
		verb: string;
		onclose: () => void;
	} = $props();

	const failures = $derived(result?.results.filter((row) => !row.ok) ?? []);
</script>

<Modal open={result !== null} title={controlText.processResult} size="sm" {onclose}>
	{#if result}
		<p class="flex items-center gap-2 text-sm font-semibold {result.failed === 0 ? 'text-success-700' : 'text-slate-800'}">
			{#if result.failed === 0}
				<SuccessMark />
			{:else}
				<i class="ti ti-alert-triangle text-xl" aria-hidden="true"></i>
			{/if}
			{summarize(result, verb)}
		</p>
		{#if failures.length > 0}
			<ul class="mt-3 divide-y divide-danger-200 rounded-lg border border-danger-200 bg-danger-50">
				{#each failures as row (row.row)}
					<li class="px-3 py-2 text-xs">
						<p class="font-semibold text-danger-700">{names[row.row - 1] ?? format(controlText.bulkRow, { row: row.row })}</p>
						<p class="text-slate-600">{row.error}</p>
					</li>
				{/each}
			</ul>
		{/if}
	{/if}
	{#snippet footer()}
		<Button label={actionText.close} variant="primary" onclick={onclose} />
	{/snippet}
</Modal>
