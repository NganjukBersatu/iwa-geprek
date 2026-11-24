<script lang="ts">
	import { untrack } from 'svelte';
	import { api } from '$lib/api';
	import type { Batch, BatchInput, BatchShiftCode, BatchUser } from '$lib/api/types';
	import { userMessage } from '$lib/api/user-message';
	import Banner from '$lib/components/card/Banner.svelte';
	import Button from '$lib/components/button/Button.svelte';
	import CancelButton from '$lib/components/button/CancelButton.svelte';
	import IconButton from '$lib/components/button/IconButton.svelte';
	import SaveButton from '$lib/components/button/SaveButton.svelte';
	import BranchField from '$lib/components/form/BranchField.svelte';
	import CheckRow from '$lib/components/form/CheckRow.svelte';
	import { FieldErrors, focusRefused } from '$lib/components/form/field-errors.svelte';
	import FormPage from '$lib/components/form/FormPage.svelte';
	import FormSection from '$lib/components/form/FormSection.svelte';
	import SelectField from '$lib/components/form/SelectField.svelte';
	import TextField from '$lib/components/form/TextField.svelte';
	import { todayIso } from '$lib/date/range';
	import { PAGES, batchPath, tasksTabPath } from '$lib/nav/pages';
	import { whenChanged } from '$lib/stores/when-changed.svelte';
	import { actionText } from '$lib/text/actions';
	import { batchText } from '$lib/text/batches';
	import { format } from '$lib/text/format';
	import { termText } from '$lib/text/terms';
	import { FILL_MODES, FILL_ONE, ITEM_KINDS, REPEAT_UNITS, TARGET_SHIFT, TARGET_USER, TARGETS, repeatLabel, type BatchKind, type RepeatUnit } from '../constants';
	import BatchUserPicker from './BatchUserPicker.svelte';
	import ShiftCodeBadge from '$lib/components/card/ShiftCodeBadge.svelte';

	let {
		kind,
		batch,
		busy,
		error,
		fieldErrors = {},
		onsave,
		onclose
	}: {
		kind: BatchKind;
		batch: Batch | null;
		busy: boolean;
		error: string;
		/** What the server refused, by field name, shown under the field itself. */
		fieldErrors?: Record<string, string>;
		onsave: (body: BatchInput, outletId: string) => void;
		onclose: () => void;
	} = $props();

	type Draft = { uid: number; id: string | null; label: string; kind: string; required: boolean };

	let nextUid = 1;
	const draft = (label = '', itemKind = 'toggle', required = true, id: string | null = null): Draft => ({ uid: nextUid++, id, label, kind: itemKind, required });
	const current = untrack(() => batch);
	const text = batchText.kinds[untrack(() => kind)];
	const routine = untrack(() => kind) === 'routine';
	const trail = [
		{ label: PAGES.tasks.label, href: tasksTabPath(routine ? 'routine' : 'outlet') },
		...(current ? [{ label: current.name, href: batchPath(current.id) }, { label: actionText.edit }] : [{ label: text.add }])
	];

	let outletId = $state(current?.outlet_id ?? '');
	let name = $state(current?.name ?? '');
	let start = $state(current?.start_clock ?? '06:00');
	let end = $state(current?.end_clock ?? '10:00');
	let active = $state(current?.is_active ?? true);

	// An old task has no unit of repeating; the form proposes every day from today and replaces the old pattern when it is saved.
	const legacy = current !== null && current.repeat_unit === null;
	const unitOf = (value: string | null | undefined): RepeatUnit => REPEAT_UNITS.find((unit) => unit.value === value)?.value ?? 'day';
	let unit = $state<string>(unitOf(current?.repeat_unit));
	let every = $state(String(current?.repeat_every ?? 1));
	let startsOn = $state(current?.starts_on ?? todayIso());
	const unitRule = $derived(REPEAT_UNITS.find((item) => item.value === unit) ?? REPEAT_UNITS[0]!);
	const preview = $derived(startsOn && Number.isInteger(Number(every)) && Number(every) >= 1 ? repeatLabel({ repeat_unit: unit, repeat_every: Number(every), starts_on: startsOn, weekdays: [] }) : '');
	let items = $state<Draft[]>(current ? current.items.map((item) => draft(item.label, item.kind, item.required, item.id)) : [draft()]);

	let fillMode = $state(current?.fill_mode ?? FILL_ONE);
	let target = $state(current?.target ?? TARGET_SHIFT);
	let people = $state<BatchUser[]>(current ? [...current.user] : []);
	const named = $derived(target === TARGET_USER);
	let codeIds = $state<string[]>(current ? current.shift_codes.map((code) => code.id) : []);
	let codes = $state<BatchShiftCode[]>([]);
	let codesLoading = $state(false);
	let codesError = $state('');
	let codesFor = '';

	const toggleCode = (id: string) => (codeIds = codeIds.includes(id) ? codeIds.filter((item) => item !== id) : [...codeIds, id]);
	const fillHint = $derived(
		fillMode === FILL_ONE ? (named ? batchText.fillOneUser : batchText.fillOneShift) : named ? batchText.fillEachUser : batchText.fillEachShift
	);

	/** The first item answers to the field's own name, which is what the server names; the items after it get a number. */
	const itemField = (index: number) => (index === 0 ? 'label' : `label_${index}`);
	const errors = new FieldErrors(
		() => ({
			outlet_id: termText.branch,
			name: format(batchText.nameOf, { noun: text.noun }),
			start_clock: batchText.startTime,
			end_clock: batchText.endTime,
			starts_on: batchText.startsOn,
			repeat_every: batchText.repeatEvery,
			shift_code_ids: batchText.shiftCodes,
			user_ids: batchText.recipients,
			items: termText.item,
			...Object.fromEntries(items.map((_, index) => [itemField(index), format(batchText.itemNameNumber, { number: index + 1 })]))
		}),
		() => fieldErrors
	);

	// A refusal from the server puts the cursor in the first refused box.
	$effect(() => {
		if (Object.keys(fieldErrors).length > 0) void focusRefused();
	});

	/** The shift codes of the chosen branch; a choice that is not in that branch is let go so it is never sent. */
	async function loadCodes(branchId: string): Promise<void> {
		codesFor = branchId;
		codesError = '';
		if (!branchId) {
			codes = [];
			codeIds = [];
			return;
		}
		codesLoading = true;
		try {
			const found = await api.batches.shiftCodeOptions(branchId);
			if (codesFor !== branchId) return;
			codes = found;
			codeIds = codeIds.filter((id) => found.some((code) => code.id === id));
		} catch (failure) {
			if (codesFor === branchId) codesError = userMessage(failure, batchText.shiftCodesFailed);
		} finally {
			if (codesFor === branchId) codesLoading = false;
		}
	}

	whenChanged(
		() => (routine ? outletId : null),
		(branchId) => {
			if (branchId !== null) void loadCodes(branchId);
		}
	);

	function move(index: number, step: -1 | 1): void {
		const to = index + step;
		if (to < 0 || to >= items.length) return;
		const copy = [...items];
		[copy[index], copy[to]] = [copy[to]!, copy[index]!];
		items = copy;
	}

	function validate(): Record<string, string> {
		const found: Record<string, string> = {};
		if (!current && !outletId) found.outlet_id = batchText.branchRequired;
		if (!name.trim()) found.name = batchText.nameRequired;
		if (routine && !named && codeIds.length === 0) found.shift_code_ids = batchText.shiftCodeRequired;
		if (routine && named && people.length === 0) found.user_ids = batchText.userRequired;
		if (!start) found.start_clock = batchText.startRequired;
		if (!end) found.end_clock = batchText.endRequired;
		else if (start && start === end) found.end_clock = batchText.endDiffersFromStart;
		if (!startsOn) found.starts_on = batchText.startsOnRequired;
		const count = Number(every);
		if (!Number.isInteger(count) || count < 1 || count > unitRule.max) found.repeat_every = format(batchText.repeatEveryInvalid, { max: unitRule.max, unit: unitRule.label });
		if (items.length === 0) found.items = batchText.itemRequired;
		items.forEach((item, index) => {
			if (!item.label.trim()) found[itemField(index)] = batchText.itemNameRequired;
		});
		return found;
	}

	// After a refused send the fields are checked again as they change, so a mark goes away once its field is right.
	let tried = $state(false);
	$effect(() => {
		const found = validate();
		if (tried) errors.refresh(found);
	});

	function submit(): void {
		tried = true;
		if (!errors.check(validate())) return;
		onsave(
			{
				kind,
				fill_mode: routine ? fillMode : FILL_ONE,
				target: routine ? target : TARGET_SHIFT,
				shift_code_ids: routine && !named ? codeIds : [],
				user_ids: routine && named ? people.map((person) => person.id) : [],
				name: name.trim(),
				start_clock: start,
				end_clock: end,
				repeat_unit: unitRule.value,
				repeat_every: Number(every),
				starts_on: startsOn,
				is_active: active,
				items: items.map((item) => ({ id: item.id, label: item.label.trim(), kind: item.kind, required: item.required }))
			},
			outletId
		);
	}
</script>

<FormPage title={current ? format(batchText.editTitleOf, { noun: text.noun, name: current.name }) : text.add} description={batchText.formDescription} stacked {trail} {busy} {onclose}>
	<FormSection icon="building-store" title={text.title} description={batchText.nameSectionDescription}>
		{#if !current}
			<BranchField bind:value={outletId} error={errors.get('outlet_id')} />
		{/if}
		<TextField label={format(batchText.nameOf, { noun: text.noun })} bind:value={name} placeholder={text.namePlaceholder} maxlength={100} required error={errors.get('name')} />
		<div class="grid gap-2 tablet:grid-cols-2">
			<TextField label={batchText.startTime} type="time" bind:value={start} error={errors.get('start_clock')} />
			<TextField label={batchText.endTime} type="time" bind:value={end} hint={batchText.endTimeHint} error={errors.get('end_clock')} />
		</div>
		<CheckRow label={batchText.activeShownToEmployees} checked={active} onchange={() => (active = !active)} />
	</FormSection>
	<FormSection icon="repeat" title={batchText.repeatSection} description={batchText.repeatSectionDescription}>
		<div class="grid gap-2 tablet:grid-cols-3">
			<TextField label={batchText.startsOn} type="date" bind:value={startsOn} required error={errors.get('starts_on')} />
			<TextField label={batchText.repeatEvery} type="number" inputmode="numeric" bind:value={every} required error={errors.get('repeat_every')} />
			<SelectField label={batchText.repeatUnit} bind:value={unit} options={REPEAT_UNITS} />
		</div>
		{#if preview}<p class="text-xs text-slate-600">{format(batchText.repeatPreview, { preview })}</p>{/if}
		{#if legacy && current}
			<p class="text-xs text-warning-700">{format(batchText.legacyRepeat, { old: repeatLabel(current) })}</p>
		{/if}
	</FormSection>
	{#if routine}
		<FormSection icon="users" title={batchText.recipientSection} description={batchText.recipientSectionDescription}>
			<div>
				<span class="text-xs font-semibold text-slate-600">{batchText.recipients}</span>
				<div class="mt-1 flex flex-wrap items-center gap-2">
					{#each TARGETS as option (option.value)}
						<Button label={option.label} active={target === option.value} onclick={() => (target = option.value)} />
					{/each}
				</div>
			</div>
			{#if named}
				<div tabindex="-1" aria-invalid={errors.get('user_ids') ? true : undefined}>
					{#if outletId}
						<BatchUserPicker bind:picked={people} {outletId} />
						<p class="mt-1 text-xs text-slate-500">{batchText.userHint}</p>
					{:else}
						<p class="text-xs text-slate-500">{batchText.userNeedsBranch}</p>
					{/if}
					{#if errors.get('user_ids')}<p class="mt-1 text-xs text-danger-700" role="alert">{errors.get('user_ids')}</p>{/if}
				</div>
			{:else}
				<div tabindex="-1" aria-invalid={errors.get('shift_code_ids') ? true : undefined}>
					<span class="text-xs font-semibold text-slate-600">{batchText.shiftCodes} <span class="text-danger-600" aria-hidden="true">*</span></span>
					<p class="mt-0.5 text-xs text-slate-500">{batchText.shiftCodesHint}</p>
					<div class="mt-2">
						{#if !outletId}
							<p class="text-xs text-slate-500">{batchText.shiftCodesNeedBranch}</p>
						{:else if codesLoading}
							<p class="text-xs text-slate-500" role="status">{batchText.shiftCodesLoading}</p>
						{:else if codesError}
							<Banner tone="danger" icon="alert-triangle" title={batchText.shiftCodesFailedTitle}>
								{codesError}
								{#snippet action()}
									<Button label={actionText.retry} onclick={() => void loadCodes(outletId)} />
								{/snippet}
							</Banner>
						{:else if codes.length === 0}
							<Banner tone="warning" icon="alert-triangle" title={batchText.shiftCodesNoneTitle}>
								{batchText.shiftCodesNone}
								{#snippet action()}
									<Button label={batchText.openShiftCodes} href={PAGES.shiftCodes.path} />
								{/snippet}
							</Banner>
						{:else}
							<div class="flex flex-col gap-0.5">
								{#each codes as code (code.id)}
									<label class="flex cursor-pointer items-center gap-2.5 rounded-lg p-2 hover:bg-brand-page">
										<input type="checkbox" checked={codeIds.includes(code.id)} onchange={() => toggleCode(code.id)} class="size-4 shrink-0 accent-brand" />
										<ShiftCodeBadge {code} showTime />
									</label>
								{/each}
							</div>
						{/if}
					</div>
					{#if errors.get('shift_code_ids')}<p class="mt-1 text-xs text-danger-700" role="alert">{errors.get('shift_code_ids')}</p>{/if}
				</div>
			{/if}
			<div>
				<span class="text-xs font-semibold text-slate-600">{batchText.fillerLabel}</span>
				<div class="mt-1 flex flex-wrap items-center gap-2">
					{#each FILL_MODES as mode (mode.value)}
						<Button label={mode.label} active={fillMode === mode.value} onclick={() => (fillMode = mode.value)} />
					{/each}
				</div>
				<p class="mt-1 text-xs text-slate-500">{fillHint}</p>
			</div>
		</FormSection>
	{/if}
	<FormSection icon="list-check" title={termText.item} description={batchText.itemsDescription}>
		{#each items as item, index (item.uid)}
			<div class="flex flex-col gap-2 rounded-lg border border-slate-200 p-3">
				<div class="flex items-center gap-2">
					<span class="flex size-7 shrink-0 items-center justify-center rounded-full bg-brand-soft text-xs font-semibold text-brand">{index + 1}</span>
					<div class="min-w-0 flex-1">
						<TextField compact label={format(batchText.itemNameNumber, { number: index + 1 })} placeholder={batchText.itemNameExample} maxlength={200} bind:value={item.label} error={errors.get(itemField(index))} />
					</div>
					<div class="flex shrink-0 gap-1">
						<IconButton icon="chevron-up" label={format(batchText.moveItemUp, { number: index + 1 })} disabled={index === 0} onclick={() => move(index, -1)} />
						<IconButton icon="chevron-down" label={format(batchText.moveItemDown, { number: index + 1 })} disabled={index === items.length - 1} onclick={() => move(index, 1)} />
						<IconButton icon="trash" label={format(batchText.removeItemNumber, { number: index + 1 })} tone="danger" disabled={items.length === 1} onclick={() => (items = items.filter((entry) => entry.uid !== item.uid))} />
					</div>
				</div>
				<div class="flex flex-wrap items-center gap-3 pl-9">
					<SelectField label={format(batchText.itemKindNumber, { number: index + 1 })} compact bind:value={item.kind} options={ITEM_KINDS} />
					<CheckRow label={batchText.mustFill} checked={item.required} onchange={() => (item.required = !item.required)} />
				</div>
			</div>
		{/each}
		<Button label={batchText.addItem} icon="plus" onclick={() => (items = [...items, draft()])} class="w-fit" />
		{#if errors.get('items')}<p class="text-xs text-danger-700" role="alert">{errors.get('items')}</p>{/if}
	</FormSection>
	{#if error && errors.count === 0}
		<div class="mt-4"><Banner tone="danger" icon="alert-triangle">{error}</Banner></div>
	{/if}

	{#snippet footer()}
		<SaveButton label={current ? batchText.saveChanges : text.add} {busy} onclick={submit} />
		<CancelButton disabled={busy} onclick={onclose} />
	{/snippet}
</FormPage>
