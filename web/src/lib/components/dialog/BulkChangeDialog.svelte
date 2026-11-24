<script lang="ts">
	import { termText } from '$lib/text/terms';
	import CancelButton from '$lib/components/button/CancelButton.svelte';
	import SaveButton from '$lib/components/button/SaveButton.svelte';
	import { parseDay } from '$lib/date/parse';
	import { parseNumber } from '$lib/format/number';
	import { untrack } from 'svelte';
	import Button from '../button/Button.svelte';
	import SelectField from '../form/SelectField.svelte';
	import TextField from '../form/TextField.svelte';
	import type { Field } from '../form/types';
	import Modal from './Modal.svelte';
	import { controlText } from '$lib/text/controls';
	import { format } from '$lib/text/format';

	let {
		count,
		fields,
		busy = false,
		error = '',
		onsubmit,
		onclose
	}: {
		count: number;
		fields: Field[];
		busy?: boolean;
		error?: string;
		onsubmit: (changes: Record<string, string | number | boolean>) => void;
		onclose: () => void;
	} = $props();

	let included = $state<Record<string, boolean>>(untrack(() => Object.fromEntries(fields.map((field) => [field.key, false]))));
	let values = $state<Record<string, string>>(untrack(() => Object.fromEntries(fields.map((field) => [field.key, field.kind === 'toggle' ? 'yes' : '']))));
	let problem = $state('');

	function submit(): void {
		const changes: Record<string, string | number | boolean> = {};
		for (const field of fields) {
			if (!included[field.key]) continue;
			const raw = (values[field.key] ?? '').trim();
			if (field.kind === 'toggle') changes[field.key] = raw !== 'no';
			else if (field.kind === 'number') {
				const parsed = parseNumber(raw);
				if (parsed === null) {
					problem = format(controlText.mustBeNumber, { name: field.label });
					return;
				}
				changes[field.key] = parsed;
			} else if (field.kind === 'date') {
				const day = parseDay(raw);
				if (!day.ok) {
					problem = day.message;
					return;
				}
				changes[field.key] = day.iso;
			} else changes[field.key] = raw;
		}
		if (Object.keys(changes).length === 0) {
			problem = controlText.changeColumnsTitle;
			return;
		}
		problem = '';
		onsubmit(changes);
	}
</script>

<Modal open title={format(controlText.changeSelectedRows, { count: count })} description={controlText.changeColumnsHint} size="sm" {busy} {onclose}>
	<div class="flex flex-col gap-4">
		{#each fields as field (field.key)}
			<div class="flex flex-col gap-2 rounded-lg border border-slate-200 p-3 {included[field.key] ? 'border-brand-line bg-brand-page' : ''}">
				<label class="flex cursor-pointer items-center gap-2 text-sm font-semibold text-slate-700">
					<input type="checkbox" bind:checked={included[field.key]} class="size-4 accent-brand" />
					{field.label}
				</label>
				{#if included[field.key]}
					{#if field.kind === 'toggle'}
						<SelectField label={field.label} compact bind:value={values[field.key]} options={[{ value: 'yes', label: field.yes ?? termText.yes }, { value: 'no', label: field.no ?? termText.no }]} />
					{:else if field.kind === 'select'}
						<SelectField label={field.label} compact bind:value={values[field.key]} options={field.options ?? []} empty={controlText.choose} />
					{:else}
						<TextField label={field.label} bind:value={values[field.key]} inputmode={field.kind === 'number' ? 'decimal' : 'text'} placeholder={field.placeholder ?? (field.kind === 'date' ? 'dd/mm/yyyy' : undefined)} />
					{/if}
				{/if}
			</div>
		{/each}
	</div>
	{#if problem || error}
		<p class="mt-3 rounded-lg border border-danger-200 bg-danger-50 px-3 py-2 text-xs text-danger-700" role="alert">{problem || error}</p>
	{/if}
	{#snippet footer()}
		<CancelButton disabled={busy} onclick={onclose} />
		<SaveButton label={controlText.apply} busy={busy} onclick={submit} />
	{/snippet}
</Modal>
