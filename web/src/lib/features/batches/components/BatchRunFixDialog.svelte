<script lang="ts">
	import { untrack } from 'svelte';
	import type { RunAnswerInput } from '$lib/api/batches';
	import type { StoredRun } from '$lib/api/types';
	import Button from '$lib/components/button/Button.svelte';
	import Modal from '$lib/components/dialog/Modal.svelte';
	import PhotoField from '$lib/components/form/PhotoField.svelte';
	import TextField from '$lib/components/form/TextField.svelte';
	import { actionText } from '$lib/text/actions';
	import { batchRunText } from '$lib/text/batch-runs';
	import { format } from '$lib/text/format';
	import { NUMBER_KIND, PHOTO_KIND, TOGGLE_KIND, TOGGLE_OPTIONS } from '../constants';

	/** The form to correct one filling: the same fields as the employee app, filled with the saved answers; the old photo stays unless it is replaced. */
	let { stored, busy, error, onsave, onclose }: { stored: StoredRun; busy: boolean; error: string; onsave: (answers: RunAnswerInput[]) => void; onclose: () => void } = $props();

	const start = untrack(() => stored);
	const items = start.batch.items;
	const saved = new Map(start.answers.map((answer) => [answer.item_id, answer]));

	let values = $state<Record<string, string>>(Object.fromEntries(items.map((item) => [item.id, saved.get(item.id)?.value ?? ''])));
	let files = $state<Record<string, File | null>>(Object.fromEntries(items.map((item) => [item.id, null])));
	let problem = $state('');

	const keptPhoto = (itemId: string): string | null => saved.get(itemId)?.photo_url ?? null;
	const empty = (item: (typeof items)[number]): boolean => (item.kind === PHOTO_KIND ? !files[item.id] && !keptPhoto(item.id) : !(values[item.id] ?? '').trim());

	function submit(): void {
		const missing = items.filter((item) => item.required && empty(item));
		if (missing.length > 0) {
			problem = format(batchRunText.missing, { labels: missing.map((item) => item.label).join(', ') });
			return;
		}
		problem = '';
		onsave(
			items.flatMap((item): RunAnswerInput[] => {
				if (empty(item)) return [];
				if (item.kind === PHOTO_KIND) return [{ item_id: item.id, value: null, file: files[item.id] ?? null, keepPhoto: !files[item.id] }];
				return [{ item_id: item.id, value: (values[item.id] ?? '').trim(), file: null, keepPhoto: false }];
			})
		);
	}
</script>

<Modal open title={format(batchRunText.fixTitle, { name: start.batch.name })} size="md" {busy} {onclose}>
	<div class="flex flex-col gap-4">
		<p class="text-xs text-slate-500">{batchRunText.fixNote}</p>
		{#each items as item (item.id)}
			{@const label = item.required ? item.label : format(batchRunText.optionalSuffix, { label: item.label })}
			{#if item.kind === TOGGLE_KIND}
				<div>
					<span class="text-xs font-semibold text-slate-600">{label}</span>
					<div class="mt-1 flex flex-wrap gap-2">
						{#each TOGGLE_OPTIONS as option (option.value)}
							<Button label={option.label} active={values[item.id] === option.value} disabled={busy} onclick={() => (values[item.id] = option.value)} />
						{/each}
					</div>
				</div>
			{:else if item.kind === PHOTO_KIND}
				<PhotoField {label} current={keptPhoto(item.id)} alt={item.label} bind:file={files[item.id]} disabled={busy} />
			{:else}
				<TextField {label} bind:value={values[item.id]} inputmode={item.kind === NUMBER_KIND ? 'decimal' : undefined} disabled={busy} />
			{/if}
		{/each}
	</div>

	{#if problem || error}
		<p class="mt-4 rounded-lg border border-danger-200 bg-danger-50 px-3 py-2 text-xs text-danger-700" role="alert">{problem || error}</p>
	{/if}

	{#snippet footer()}
		<Button label={actionText.cancel} disabled={busy} onclick={onclose} />
		<Button label={busy ? batchRunText.saving : batchRunText.saveFix} variant="primary" disabled={busy} onclick={submit} />
	{/snippet}
</Modal>
