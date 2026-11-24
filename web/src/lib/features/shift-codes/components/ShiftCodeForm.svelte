<script lang="ts">
	import CancelButton from '$lib/components/button/CancelButton.svelte';
	import SaveButton from '$lib/components/button/SaveButton.svelte';
	import ColorField from '$lib/components/form/ColorField.svelte';
	import TextButton from '$lib/components/button/TextButton.svelte';
	import type { CodeGroup, CodeGroupCreate, CodeGroupUpdate } from '$lib/api/types';
	import FormPage from '$lib/components/form/FormPage.svelte';
	import FormSection from '$lib/components/form/FormSection.svelte';
	import CheckRow from '$lib/components/form/CheckRow.svelte';
	import SelectField from '$lib/components/form/SelectField.svelte';
	import TextField from '$lib/components/form/TextField.svelte';
	import Banner from '$lib/components/card/Banner.svelte';
	import { FieldErrors, focusRefused } from '$lib/components/form/field-errors.svelte';
	import { PAGES, shiftCodePath } from '$lib/nav/pages';
	import { untrack } from 'svelte';
	import { SvelteSet } from 'svelte/reactivity';
	import { termText } from '$lib/text/terms';
	import { actionText } from '$lib/text/actions';
	import { shiftCodeText } from '$lib/text/shift-codes';
	import { format } from '$lib/text/format';

	let {
		group,
		outlets,
		categories,
		busy,
		error,
		fieldErrors = {},
		onsave,
		onclose
	}: {
		group: CodeGroup | null;
		outlets: { id: string; name: string }[];
		categories: string[];
		busy: boolean;
		error: string;
		/** What the server refused, by field name, shown under the field itself. */
		fieldErrors?: Record<string, string>;
		onsave: (body: CodeGroupCreate | CodeGroupUpdate) => void;
		onclose: () => void;
	} = $props();

	const DEFAULT_COLOR = getComputedStyle(document.documentElement).getPropertyValue('--color-brand').trim();
	const initial = untrack(() => ({ group, soleOutlet: outlets.length === 1 ? (outlets[0]?.id ?? '') : '' }));
	const current = initial.group;
	const trail = [
		{ label: PAGES.shiftCodes.label, href: PAGES.shiftCodes.path },
		...(current ? [{ label: current.code, href: shiftCodePath(current.id) }, { label: actionText.edit }] : [{ label: shiftCodeText.addShiftCode }])
	];

	let code = $state(current?.code ?? '');
	// Karakter kendali tidak bisa diketik, jadi nilai ini tidak pernah sama dengan nama kategori sungguhan.
	const ADD_CATEGORY = '\u0001add';
	let categoryChoice = $state(current?.category ?? '');
	let newCategory = $state('');
	const addingCategory = $derived(categoryChoice === ADD_CATEGORY);
	const categoryOptions = $derived([...categories.map((name) => ({ value: name, label: name })), { value: ADD_CATEGORY, label: shiftCodeText.addCategoryOption }]);
	const chosenCategory = $derived((addingCategory ? newCategory : categoryChoice).trim());
	let dayOff = $state(current?.is_day_off ?? false);
	let crossesMidnight = $state(current?.crosses_midnight ?? false);
	let start = $state(current?.start_clock ?? '');
	let end = $state(current?.end_clock ?? '');
	let overtimeStart = $state(current?.overtime_start_clock ?? '');
	let overtimeEnd = $state(current?.overtime_end_clock ?? '');
	let color = $state(current?.color ?? DEFAULT_COLOR);
	let order = $state(String(current?.sort_order ?? 0));
	const branches = new SvelteSet<string>(current ? current.branches.map((branch) => branch.id) : initial.soleOutlet ? [initial.soleOutlet] : []);
	const errors = new FieldErrors(
		{ code: termText.code, category: termText.category, start_clock: shiftCodeText.startTime, end_clock: shiftCodeText.endTime, overtime_start_clock: shiftCodeText.overtimeStart, overtime_end_clock: shiftCodeText.overtimeEnd, crosses_midnight: shiftCodeText.crossesMidnight, outlet_ids: termText.branch },
		() => fieldErrors
	);

	// A refusal from the server puts the cursor in the first refused box.
	$effect(() => {
		if (Object.keys(fieldErrors).length > 0) void focusRefused();
	});

	const toggleBranch = (id: string) => (branches.has(id) ? branches.delete(id) : branches.add(id));
	const allBranches = $derived(outlets.length > 0 && outlets.every((outlet) => branches.has(outlet.id)));

	function submit(): void {
		const found: Record<string, string> = {};
		if (!code.trim()) found.code = shiftCodeText.codeRequired;
		if (!chosenCategory) found.category = addingCategory ? shiftCodeText.newCategoryRequired : shiftCodeText.categoryRequired;
		if (!dayOff && !start) found.start_clock = shiftCodeText.startRequired;
		if (!dayOff && !end) found.end_clock = shiftCodeText.endRequired;
		if (!dayOff && overtimeStart && !overtimeEnd) found.overtime_end_clock = shiftCodeText.overtimeEndRequired;
		if (!dayOff && overtimeEnd && !overtimeStart) found.overtime_start_clock = shiftCodeText.overtimeStartRequired;
		// Sama dengan aturan server, supaya admin tahu sebelum mengirim; server tetap yang memutuskan.
		if (!dayOff && start && end) {
			if (end === start) found.end_clock = shiftCodeText.endSameAsStart;
			else if (end < start && !crossesMidnight) found.crosses_midnight = shiftCodeText.needsMidnight;
			else if (end > start && crossesMidnight) found.crosses_midnight = shiftCodeText.midnightUnneeded;
		}
		if (branches.size === 0) found.outlet_ids = shiftCodeText.branchRequired;
		if (!errors.check(found)) return;
		onsave({
			code: code.trim(),
			category: chosenCategory,
			start_clock: dayOff ? null : start,
			end_clock: dayOff ? null : end,
			overtime_start_clock: dayOff ? null : overtimeStart || null,
			overtime_end_clock: dayOff ? null : overtimeEnd || null,
			color,
			is_day_off: dayOff,
			crosses_midnight: dayOff ? false : crossesMidnight,
			sort_order: Math.max(0, Math.trunc(Number(order) || 0)),
			outlet_ids: [...branches]
		});
	}
</script>

<FormPage title={current ? format(shiftCodeText.editCodeTitle, { code: current.code }) : shiftCodeText.addShiftCode} description={shiftCodeText.formDescription} stacked {trail} {busy} {onclose}>
	<FormSection icon="clock" title={termText.code} description={shiftCodeText.nameSectionDescription}>
		<div class="grid gap-2 tablet:grid-cols-2">
			<TextField label={termText.code} bind:value={code} maxlength={20} placeholder="08" required error={errors.get('code')} />
			<div class="flex flex-col gap-2">
				<SelectField label={termText.category} bind:value={categoryChoice} options={categoryOptions} empty={shiftCodeText.categoryChoose} required hint={addingCategory ? undefined : shiftCodeText.categoryHint} error={addingCategory ? undefined : errors.get('category')} />
				{#if addingCategory}
					<TextField label={shiftCodeText.newCategoryName} bind:value={newCategory} maxlength={100} placeholder={shiftCodeText.categoryExample} required hint={shiftCodeText.newCategoryHint} error={errors.get('category')} />
				{/if}
			</div>
		</div>
		<CheckRow label={shiftCodeText.dayOffCode} checked={dayOff} onchange={() => (dayOff = !dayOff)} />
		{#if !dayOff}
			<div class="grid gap-2 tablet:grid-cols-2">
				<TextField label={shiftCodeText.startTime} type="time" bind:value={start} required error={errors.get('start_clock')} />
				<TextField label={shiftCodeText.endTime} type="time" bind:value={end} required hint={shiftCodeText.endTimeHint} error={errors.get('end_clock')} />
				<TextField label={shiftCodeText.overtimeStartOptional} type="time" bind:value={overtimeStart} error={errors.get('overtime_start_clock')} />
				<TextField label={shiftCodeText.overtimeEndOptional} type="time" bind:value={overtimeEnd} error={errors.get('overtime_end_clock')} />
			</div>
			<CheckRow label={shiftCodeText.crossesMidnight} hint={shiftCodeText.crossesMidnightHint} checked={crossesMidnight} onchange={() => (crossesMidnight = !crossesMidnight)} />
			{#if errors.get('crosses_midnight')}<p class="text-xs text-danger-700" role="alert">{errors.get('crosses_midnight')}</p>{/if}
		{/if}
	</FormSection>
	<FormSection icon="palette" title={shiftCodeText.display} description={shiftCodeText.displayDescription}>
		<div class="grid gap-2 tablet:grid-cols-2">
			<ColorField label={shiftCodeText.color} bind:value={color} />
			<TextField label={shiftCodeText.sortOrder} type="number" inputmode="numeric" bind:value={order} />
		</div>
	</FormSection>
	<FormSection icon="building-store" title={shiftCodeText.usedInBranches} description={shiftCodeText.usedInBranchesHint}>
		{#if outlets.length > 1}
			<span class="text-xs"><TextButton label={allBranches ? shiftCodeText.clearAll : shiftCodeText.selectAll} onclick={() => (allBranches ? branches.clear() : outlets.forEach((outlet) => branches.add(outlet.id)))} /></span>
		{/if}
		<div class="grid gap-1 tablet:grid-cols-2" tabindex="-1" aria-invalid={errors.get('outlet_ids') ? true : undefined}>
			{#each outlets as outlet (outlet.id)}
				<CheckRow label={outlet.name} checked={branches.has(outlet.id)} onchange={() => toggleBranch(outlet.id)} />
			{/each}
		</div>
		{#if errors.get('outlet_ids')}<p class="text-xs text-danger-700" role="alert">{errors.get('outlet_ids')}</p>{/if}
	</FormSection>
	{#if error && errors.count === 0}
		<div class="mt-4"><Banner tone="danger" icon="alert-triangle">{error}</Banner></div>
	{/if}

	{#snippet footer()}
		<SaveButton busy={busy} onclick={() => submit()} />
		<CancelButton disabled={busy} onclick={onclose} />
	{/snippet}
</FormPage>
