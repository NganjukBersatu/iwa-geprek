<script lang="ts">
	import type { ShiftCategory } from '$lib/api/types';
	import { ApiError } from '$lib/api/http';
	import { userMessage } from '$lib/api/user-message';
	import Badge from '$lib/components/card/Badge.svelte';
	import Banner from '$lib/components/card/Banner.svelte';
	import Notice from '$lib/components/card/Notice.svelte';
	import Button from '$lib/components/button/Button.svelte';
	import DeleteButton from '$lib/components/button/DeleteButton.svelte';
	import ConfirmDialog from '$lib/components/dialog/ConfirmDialog.svelte';
	import CancelButton from '$lib/components/button/CancelButton.svelte';
	import SaveButton from '$lib/components/button/SaveButton.svelte';
	import Modal from '$lib/components/dialog/Modal.svelte';
	import { FieldErrors, focusRefused } from '$lib/components/form/field-errors.svelte';
	import SelectField from '$lib/components/form/SelectField.svelte';
	import TextField from '$lib/components/form/TextField.svelte';
	import type { ShiftCodesState } from '../shift-codes.svelte';
	import { actionText } from '$lib/text/actions';
	import { shiftCodeText } from '$lib/text/shift-codes';
	import { termText } from '$lib/text/terms';
	import { format } from '$lib/text/format';

	let { shiftCodes }: { shiftCodes: ShiftCodesState } = $props();

	const KIND_OPTIONS = [
		{ value: '', label: shiftCodeText.kindUnset },
		{ value: 'work', label: shiftCodeText.kindWork },
		{ value: 'off', label: shiftCodeText.kindOff }
	];

	let editing = $state<ShiftCategory | null>(null);
	let removing = $state<ShiftCategory | null>(null);
	let name = $state('');
	let kind = $state('');
	let from = $state('');
	let until = $state('');
	let busy = $state(false);
	let problem = $state('');
	let refused = $state<Record<string, string>>({});

	const errors = new FieldErrors(
		{ name: termText.name, shift_kind: shiftCodeText.categoryKindLabel, start_from: shiftCodeText.startFrom, start_until: shiftCodeText.startUntil },
		() => refused
	);

	$effect(() => {
		if (Object.keys(refused).length > 0) void focusRefused();
	});

	function kindLabel(category: ShiftCategory): string {
		if (category.shift_kind === 'work') return shiftCodeText.kindWork;
		if (category.shift_kind === 'off') return shiftCodeText.kindOff;
		return shiftCodeText.kindUnset;
	}

	function edit(category: ShiftCategory): void {
		editing = category;
		name = category.name;
		kind = category.shift_kind ?? '';
		from = category.start_from ?? '';
		until = category.start_until ?? '';
		problem = '';
		refused = {};
	}

	function back(): void {
		editing = null;
		problem = '';
		refused = {};
	}

	async function remove(): Promise<void> {
		if (!removing || busy) return;
		busy = true;
		problem = '';
		try {
			await shiftCodes.removeCategory(removing);
			removing = null;
		} catch (error) {
			removing = null;
			problem = userMessage(error, shiftCodeText.categoryRemoveFailed);
		} finally {
			busy = false;
		}
	}

	async function save(): Promise<void> {
		if (!editing || busy) return;
		busy = true;
		problem = '';
		refused = {};
		try {
			await shiftCodes.saveCategory(editing.id, {
				name: name.trim(),
				shift_kind: kind === 'work' || kind === 'off' ? kind : null,
				start_from: kind === 'off' ? null : from || null,
				start_until: kind === 'off' ? null : until || null
			});
			back();
		} catch (error) {
			refused = error instanceof ApiError ? error.fieldErrors : {};
			problem = userMessage(error, shiftCodeText.categorySaveFailed);
		} finally {
			busy = false;
		}
	}
</script>

<Modal
	open
	title={editing ? format(shiftCodeText.categoryEditTitle, { name: editing.name }) : shiftCodeText.categorySettingsTitle}
	description={editing ? undefined : shiftCodeText.categorySettingsDescription}
	size="md"
	{busy}
	onclose={() => shiftCodes.closeCategories()}
>
	{#if editing}
		<div class="flex flex-col gap-3">
			<TextField label={termText.name} bind:value={name} maxlength={100} required error={errors.get('name')} />
			<SelectField label={shiftCodeText.categoryKindLabel} bind:value={kind} options={KIND_OPTIONS} hint={shiftCodeText.categoryKindHint} error={errors.get('shift_kind')} />
			{#if kind !== 'off'}
				<div class="grid gap-2 tablet:grid-cols-2">
					<TextField label={shiftCodeText.startFrom} type="time" bind:value={from} error={errors.get('start_from')} />
					<TextField label={shiftCodeText.startUntil} type="time" bind:value={until} error={errors.get('start_until')} />
				</div>
				<p class="text-xs text-slate-500">{shiftCodeText.startRangeHint}</p>
			{/if}
			{#if problem && errors.count === 0}<Banner tone="danger" icon="alert-triangle">{problem}</Banner>{/if}
		</div>
	{:else if shiftCodes.categorySettings.length === 0}
		<Notice text={shiftCodeText.categorySettingsEmpty} />
	{:else}
		<ul class="flex max-h-96 flex-col divide-y divide-slate-100 overflow-y-auto">
			{#each shiftCodes.categorySettings as category (category.id)}
				<li class="flex items-center justify-between gap-3 py-2">
					<span class="min-w-0">
						<span class="block truncate text-sm font-medium text-slate-800">{category.name}</span>
						<span class="mt-1 flex flex-wrap items-center gap-1">
							<Badge tone={category.shift_kind ? 'neutral' : 'warning'}>{kindLabel(category)}</Badge>
							{#if category.start_from && category.start_until}<Badge tone="neutral">{format(shiftCodeText.startRange, { from: category.start_from, until: category.start_until })}</Badge>{/if}
							<span class="text-xs text-slate-500">{format(shiftCodeText.codesCount, { count: category.codes })}</span>
							{#if category.mismatched > 0}<Badge tone="warning">{format(shiftCodeText.mismatchedCodes, { count: category.mismatched })}</Badge>{/if}
						</span>
					</span>
					<span class="flex shrink-0 items-center gap-1">
						<Button label={shiftCodeText.setCategory} variant="tertiary" small onclick={() => edit(category)} />
						<DeleteButton small label={shiftCodeText.deleteCategory} disabled={category.codes > 0 || busy} hint={category.codes > 0 ? format(shiftCodeText.categoryInUseHint, { count: category.codes }) : undefined} onclick={() => (removing = category)} />
					</span>
				</li>
			{/each}
		</ul>
		{#if problem}<div class="mt-3"><Banner tone="danger" icon="alert-triangle">{problem}</Banner></div>{/if}
	{/if}
	{#snippet footer()}
		{#if editing}
			<SaveButton {busy} onclick={() => void save()} />
			<CancelButton disabled={busy} onclick={back} />
		{:else}
			<Button label={actionText.close} variant="primary" onclick={() => shiftCodes.closeCategories()} />
		{/if}
	{/snippet}
</Modal>

<ConfirmDialog
	open={removing !== null}
	title={removing ? format(shiftCodeText.deleteCategoryTitle, { name: removing.name }) : ''}
	confirmLabel={shiftCodeText.deleteCategoryConfirm}
	{busy}
	onconfirm={() => void remove()}
	oncancel={() => (removing = null)}
>
	{shiftCodeText.deleteCategoryNote}
</ConfirmDialog>
