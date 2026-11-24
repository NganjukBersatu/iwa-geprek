<script lang="ts">
	import type { Batch, BatchCopyResult } from '$lib/api/types';
	import Button from '$lib/components/button/Button.svelte';
	import Banner from '$lib/components/card/Banner.svelte';
	import Modal from '$lib/components/dialog/Modal.svelte';
	import CheckRow from '$lib/components/form/CheckRow.svelte';
	import { actionText } from '$lib/text/actions';
	import { batchText } from '$lib/text/batches';
	import { format } from '$lib/text/format';
	import { TARGET_USER } from '../constants';

	let {
		batch,
		outlets,
		result,
		busy,
		error,
		oncopy,
		onclose
	}: {
		batch: Batch;
		outlets: { id: string; name: string }[];
		result: BatchCopyResult | null;
		busy: boolean;
		error: string;
		oncopy: (outletIds: string[]) => void;
		onclose: () => void;
	} = $props();

	const others = $derived(outlets.filter((outlet) => outlet.id !== batch.outlet_id));
	let picked = $state<string[]>([]);
	let problem = $state('');

	const toggle = (id: string) => (picked = picked.includes(id) ? picked.filter((item) => item !== id) : [...picked, id]);
	const allPicked = $derived(others.length > 0 && picked.length === others.length);

	function submit(): void {
		if (picked.length === 0) {
			problem = batchText.copyRequired;
			return;
		}
		problem = '';
		oncopy(picked);
	}
</script>

<Modal open title={format(batchText.copyTitle, { name: batch.name })} size="md" {busy} {onclose}>
	{#if result}
		<div class="flex flex-col gap-3">
			{#if result.created.length > 0}
				<Banner tone="success" icon="circle-check" title={format(batchText.copiedTitle, { count: result.created.length })}>
					{result.created.map((item) => item.outlet_name).join(', ')}
				</Banner>
			{/if}
			{#if result.skipped.length > 0}
				<Banner tone="warning" icon="alert-triangle" title={format(batchText.skippedTitle, { count: result.skipped.length })}>
					<ul class="mt-1 list-disc space-y-0.5 pl-4">
						{#each result.skipped as item (item.outlet_id)}
							<li>{item.outlet_name ? `${item.outlet_name}: ` : ''}{item.reason}</li>
						{/each}
					</ul>
				</Banner>
			{/if}
		</div>
	{:else if others.length === 0}
		<p class="text-sm text-slate-600">{batchText.copyNoTargets}</p>
	{:else}
		<p class="text-sm text-slate-600">
			{batchText.copyIntro}
			{#if batch.kind === 'routine' && batch.target === TARGET_USER}
				{batchText.copyUserNote}
			{:else if batch.kind === 'routine'}
				{batchText.copyShiftNote}
			{/if}
		</p>
		<div class="mt-3 flex flex-col gap-0.5">
			<CheckRow label={batchText.copyAllOthers} checked={allPicked} onchange={() => (picked = allPicked ? [] : others.map((outlet) => outlet.id))} />
			{#each others as outlet (outlet.id)}
				<CheckRow label={outlet.name} checked={picked.includes(outlet.id)} onchange={() => toggle(outlet.id)} />
			{/each}
		</div>
	{/if}

	{#if !result && (problem || error)}
		<p class="mt-4 rounded-lg border border-danger-200 bg-danger-50 px-3 py-2 text-xs text-danger-700" role="alert">{problem || error}</p>
	{/if}

	{#snippet footer()}
		{#if result || others.length === 0}
			<Button label={batchText.close} variant="primary" onclick={onclose} />
		{:else}
			<Button label={actionText.cancel} disabled={busy} onclick={onclose} />
			<Button label={busy ? batchText.copying : format(batchText.copyAction, { count: picked.length })} variant="primary" disabled={busy} onclick={submit} />
		{/if}
	{/snippet}
</Modal>
