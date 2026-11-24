<script lang="ts">
	import { controlText } from '$lib/text/controls';
	import { PAGES, variantGroupPath } from '$lib/nav/pages';
	import type { VariantGroup, VariantGroupCreate, VariantGroupUpdate } from '$lib/api/types';
	import CancelButton from '$lib/components/button/CancelButton.svelte';
	import DeleteButton from '$lib/components/button/DeleteButton.svelte';
	import SaveButton from '$lib/components/button/SaveButton.svelte';
	import Button from '$lib/components/button/Button.svelte';
	import Banner from '$lib/components/card/Banner.svelte';
	import FormPage from '$lib/components/form/FormPage.svelte';
	import FormSection from '$lib/components/form/FormSection.svelte';
	import CheckRow from '$lib/components/form/CheckRow.svelte';
	import ScopeField from '$lib/components/form/ScopeField.svelte';
	import { branches } from '$lib/stores/branch';
	import TextField from '$lib/components/form/TextField.svelte';
	import { FieldErrors, focusRefused } from '$lib/components/form/field-errors.svelte';
	import { untrack } from 'svelte';
	import { SvelteSet } from 'svelte/reactivity';
	import MenuPicker from '$lib/components/form/MenuPicker.svelte';
	import { termText } from '$lib/text/terms';
	import { actionText } from '$lib/text/actions';
	import { optionText } from '$lib/text/options';
	import { format } from '$lib/text/format';

	let {
		group,
		menus,
		busy,
		error,
		fieldErrors = {},
		onsave,
		onclose
	}: {
		group: VariantGroup | null;
		menus: { id: string; name: string }[];
		busy: boolean;
		error: string;
		/** What the server refused, by field name, shown under the field itself. */
		fieldErrors?: Record<string, string>;
		onsave: (body: VariantGroupCreate | VariantGroupUpdate) => void;
		onclose: () => void;
	} = $props();

	const COLOR = /^#[0-9a-fA-F]{6}$/;
	const current = untrack(() => group);
	const trail = [
		{ label: PAGES.options.label, href: PAGES.options.path },
		...(current ? [{ label: current.name, href: variantGroupPath(current.id) }, { label: actionText.edit }] : [{ label: optionText.addVariantGroup }])
	];

	let name = $state(current?.name ?? '');
	let scope = $state(current?.outlet_id ?? '');
	let required = $state(current?.required ?? true);
	let active = $state(current?.is_active ?? true);
	let choices = $state(current?.choices.map((choice) => ({ id: choice.id as string | null, name: choice.name, color: choice.color ?? '', is_active: choice.is_active })) ?? [{ id: null, name: '', color: '', is_active: true }]);
	const chosen = new SvelteSet<string>(current?.menu_ids ?? []);
	const errors = new FieldErrors(
		() => ({
			name: optionText.groupName,
			choices: optionText.choices,
			...Object.fromEntries(choices.flatMap((_, index) => [[`choice_name_${index}`, format(optionText.choiceNumber, { number: index + 1 })], [`color_${index}`, format(optionText.choiceColorNumber, { number: index + 1 })]]))
		}),
		() => fieldErrors
	);

	// A refusal from the server puts the cursor in the first refused box.
	$effect(() => {
		if (Object.keys(fieldErrors).length > 0) void focusRefused();
	});

	const addChoice = () => (choices = [...choices, { id: null, name: '', color: '', is_active: true }]);
	const removeChoice = (index: number) => (choices = choices.filter((_, position) => position !== index));

	function submit(): void {
		const found: Record<string, string> = {};
		if (!name.trim()) found.name = optionText.groupNameRequired;
		const filled = choices.filter((choice) => choice.name.trim());
		if (filled.length === 0) found.choice_name_0 = optionText.choiceRequired;
		choices.forEach((choice, index) => {
			if (choice.color && !COLOR.test(choice.color)) found[`color_${index}`] = 'Warna harus berbentuk #RRGGBB, enam digit angka atau huruf A sampai F.';
		});
		if (!errors.check(found)) return;
		onsave({
			name: name.trim(),
			required,
			is_active: active,
			choices: filled.map((choice) => ({ id: choice.id, name: choice.name.trim(), color: choice.color || null, is_active: choice.is_active })),
			menu_ids: [...chosen],
			outlet_id: scope || null
		});
	}
</script>

<FormPage title={current ? format(controlText.editName, { name: current.name }) : optionText.addVariantGroup} description={optionText.groupFormDescription} stacked {trail} {busy} {onclose}>
	<FormSection icon="list-details" title={optionText.group} description={optionText.groupSectionDescription}>
		<TextField label={optionText.groupName} bind:value={name} maxlength={80} required error={errors.get('name')} />
		<ScopeField bind:value={scope} outlets={$branches} hint={optionText.groupScopeHint} />
		<div class="grid gap-2 tablet:grid-cols-2">
			<CheckRow label={optionText.mustChoose} hint={optionText.mustChooseHint} checked={required} onchange={() => (required = !required)} />
			<CheckRow label={termText.active} checked={active} onchange={() => (active = !active)} />
		</div>
	</FormSection>
	<FormSection icon="list-check" title={optionText.choices} description={optionText.choicesDescription}>
		{#each choices as choice, index (index)}
			<div class="grid items-end gap-2 tablet:grid-cols-[1fr_8rem_auto_auto]">
				<TextField label={format(optionText.choiceNumber, { number: index + 1 })} bind:value={choice.name} maxlength={60} error={errors.get(`choice_name_${index}`)} />
				<TextField label={optionText.color} bind:value={choice.color} error={errors.get(`color_${index}`)} />
				<CheckRow label={termText.active} checked={choice.is_active} onchange={() => (choice.is_active = !choice.is_active)} />
				<DeleteButton small disabled={choices.length === 1} onclick={() => removeChoice(index)} />
			</div>
		{/each}
		<Button label={optionText.addChoice} icon="plus" variant="tertiary" small compact onclick={addChoice} class="w-fit" />
	</FormSection>
	<FormSection icon="cup" title={termText.menu} description={optionText.groupMenusDescription}>
		<MenuPicker {menus} {chosen} label={optionText.usedOnMenus} />
	</FormSection>
	{#if error && errors.count === 0}
		<div class="mt-4"><Banner tone="danger" icon="alert-triangle">{error}</Banner></div>
	{/if}

	{#snippet footer()}
		<SaveButton busy={busy} onclick={submit} />
		<CancelButton disabled={busy} onclick={onclose} />
	{/snippet}
</FormPage>
