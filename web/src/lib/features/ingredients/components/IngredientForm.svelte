<script lang="ts">
	import { controlText } from '$lib/text/controls';
	import Banner from '$lib/components/card/Banner.svelte';
	import CheckRow from '$lib/components/form/CheckRow.svelte';
	import type { Ingredient, IngredientCreate, IngredientOptions, IngredientUpdate } from '$lib/api/types';
	import CancelButton from '$lib/components/button/CancelButton.svelte';
	import SaveButton from '$lib/components/button/SaveButton.svelte';
	import Button from '$lib/components/button/Button.svelte';
	import FormPage from '$lib/components/form/FormPage.svelte';
	import FormSection from '$lib/components/form/FormSection.svelte';
	import BranchField from '$lib/components/form/BranchField.svelte';
	import MoneyField from '$lib/components/form/MoneyField.svelte';
	import PhotoField from '$lib/components/form/PhotoField.svelte';
	import SelectField from '$lib/components/form/SelectField.svelte';
	import TextField from '$lib/components/form/TextField.svelte';
	import { PAGES, ingredientPath } from '$lib/nav/pages';
	import { FieldErrors, focusRefused } from '$lib/components/form/field-errors.svelte';
	import { parseNumber } from '$lib/format/number';
	import { untrack } from 'svelte';
	import { termText } from '$lib/text/terms';
	import { actionText } from '$lib/text/actions';
	import { ingredientText } from '$lib/text/ingredients';
	import { format } from '$lib/text/format';

	let {
		ingredient,
		options,
		canEverywhere = false,
		busy,
		error,
		fieldErrors = {},
		onsave,
		onremovephoto,
		indirectDefault = false,
		onclose
	}: {
		ingredient: Ingredient | null;
		options: IngredientOptions;
		canEverywhere?: boolean;
		busy: boolean;
		error: string;
		/** What the server refused, by field name, shown under the field itself. */
		fieldErrors?: Record<string, string>;
		onsave: (body: IngredientCreate | IngredientUpdate, photo: File | null, everywhere: boolean, outletId: string) => void;
		onremovephoto: () => void;
		/** Daftar Bahan Tidak Langsung membuka form baru dengan centang tidak langsung sudah menyala. */
		indirectDefault?: boolean;
		onclose: () => void;
	} = $props();

	const MAX_SHRINK = 100;
	const current = untrack(() => ingredient);
	// Bahan tidak langsung punya daftar sendiri, jadi jejaknya kembali ke Bahan Tidak Langsung.
	const listPage = (current?.is_indirect ?? untrack(() => indirectDefault)) ? PAGES.indirectIngredients : PAGES.ingredients;
	const trail = [
		{ label: listPage.label, href: listPage.path },
		...(current?.category ? [{ label: current.category }] : []),
		...(current ? [{ label: current.name, href: ingredientPath(current.id) }, { label: actionText.edit }] : [{ label: controlText.addIngredient }])
	];

	let name = $state(current?.name ?? '');
	let unit = $state(current?.unit_id ?? '');
	let category = $state(current?.category_id ?? '');
	let packagePrice = $state(current ? String(Math.round(Number(current.package_price))) : '');
	let packageSize = $state(current ? String(Number(current.package_size)) : '1');
	let unitPrice = $state(current ? String(Number(current.unit_price)) : '');
	let shrink = $state(current ? String(Number(current.shrink_tolerance)) : '0');
	let minimum = $state(current ? String(Number(current.minimum)) : '0');
	let active = $state(current?.is_active ?? true);
	let available = $state(current?.is_available ?? true);
	let indirect = $state(current?.is_indirect ?? untrack(() => indirectDefault));
	let photo = $state<File | null>(null);
	let everywhere = $state(false);
	let outletId = $state('');
	const errors = new FieldErrors(
		{
			outlet_id: termText.branch,
			name: ingredientText.ingredientName,
			unit_id: termText.unit,
			category_id: termText.category,
			package_price: ingredientText.packagePrice,
			package_size: ingredientText.packageSize,
			unit_price: ingredientText.unitPrice,
			shrink_tolerance: ingredientText.shrinkTolerance,
			minimum: ingredientText.minimumLimit
		},
		() => fieldErrors
	);

	// A refusal from the server puts the cursor in the first refused box.
	$effect(() => {
		if (Object.keys(fieldErrors).length > 0) void focusRefused();
	});

	const shared = $derived(current !== null && current.branch_count > 1);
	const unitChoices = $derived(options.units.map((item) => ({ value: item.id, label: item.name })));
	const categoryChoices = $derived(options.categories.map((item) => ({ value: item.id, label: item.name })));

	function submit(): void {
		const found: Record<string, string> = {};
		const size = parseNumber(packageSize);
		const price = parseNumber(packagePrice || '0');
		const perUnit = unitPrice.trim() ? parseNumber(unitPrice) : null;
		const tolerance = parseNumber(shrink || '0');
		const least = parseNumber(minimum || '0');
		if (!current && !everywhere && !outletId) found.outlet_id = ingredientText.branchRequired;
		if (!name.trim()) found.name = ingredientText.nameRequired;
		if (!unit) found.unit_id = ingredientText.unitRequired;
		if (price === null || price < 0) found.package_price = ingredientText.packagePriceInvalid;
		if (size === null || size <= 0) found.package_size = ingredientText.packageSizeInvalid;
		if (unitPrice.trim() && (perUnit === null || perUnit < 0)) found.unit_price = ingredientText.unitPriceInvalid;
		if (tolerance === null || tolerance < 0 || tolerance > MAX_SHRINK) found.shrink_tolerance = format(ingredientText.shrinkInvalid, { max: MAX_SHRINK });
		if (least === null || least < 0) found.minimum = ingredientText.minimumInvalid;
		if (!errors.check(found)) return;
		if (size === null || price === null || tolerance === null || least === null) return;
		const body = {
			name: name.trim(),
			unit_id: unit,
			category_id: category || null,
			package_price: String(price),
			package_size: String(size),
			shrink_tolerance: String(tolerance),
			minimum: String(least),
			is_indirect: indirect
		};
		if (!current) return onsave({ ...body, unit_price: perUnit === null ? null : String(perUnit) }, photo, everywhere, outletId);
		onsave({ ...body, unit_price: perUnit === null ? undefined : String(perUnit), is_active: active, is_available: available }, photo, false, current.outlet_id);
	}
</script>

<FormPage title={current ? format(controlText.editName, { name: current.name }) : controlText.addIngredient} description={ingredientText.formDescription} stacked {trail} {busy} {onclose}>
	<FormSection icon="package" title={termText.ingredient} description={ingredientText.nameSectionDescription}>
		{#if !current && !everywhere}
			<BranchField bind:value={outletId} error={errors.get('outlet_id')} />
		{/if}
		<div class="grid gap-2 tablet:grid-cols-2">
			<TextField label={ingredientText.ingredientName} bind:value={name} maxlength={255} required error={errors.get('name')} />
			<SelectField label={termText.unit} bind:value={unit} options={unitChoices} empty={ingredientText.chooseUnit} required error={errors.get('unit_id')} />
		</div>
		{#if shared}
			<p class="rounded-lg bg-brand-page px-3 py-2 text-xs text-slate-600">{format(ingredientText.ingredientUsedInBranches, { count: current?.branch_count ?? '' })}</p>
		{/if}
		<div class="grid gap-2 tablet:grid-cols-2 tablet:items-end">
			<SelectField label={termText.category} bind:value={category} options={categoryChoices} empty={termText.noCategory} error={errors.get('category_id')} />
			{#if current}
				<div class="flex flex-wrap items-center gap-x-6 gap-y-2 tablet:h-10">
					<CheckRow label={termText.active} checked={active} onchange={() => (active = !active)} />
					<CheckRow label={ingredientText.available} checked={available} onchange={() => (available = !available)} />
				</div>
			{:else if canEverywhere}
				<CheckRow label={ingredientText.addToAllBranches} hint={ingredientText.addToAllBranchesHint} checked={everywhere} onchange={() => (everywhere = !everywhere)} />
			{/if}
		</div>
	</FormSection>
	<FormSection icon="cash" title={termText.price} description={ingredientText.priceSectionDescription}>
		<div class="grid gap-2 tablet:grid-cols-3">
			<MoneyField label={ingredientText.packagePriceRupiah} bind:value={packagePrice} error={errors.get('package_price')} />
			<TextField label={ingredientText.packageSize} inputmode="decimal" bind:value={packageSize} hint={ingredientText.packageSizeHint} error={errors.get('package_size')} />
			<TextField label={ingredientText.unitPriceRupiah} inputmode="decimal" bind:value={unitPrice} hint={ingredientText.unitPriceHint} error={errors.get('unit_price')} />
		</div>
	</FormSection>
	<FormSection icon="box" title={termText.stock} description={ingredientText.stockSectionDescription}>
		<div class="grid gap-2 tablet:grid-cols-2">
			<TextField label={ingredientText.shrinkTolerancePercent} inputmode="decimal" bind:value={shrink} hint={ingredientText.shrinkToleranceHint} error={errors.get('shrink_tolerance')} />
			<TextField label={ingredientText.minimumLimit} inputmode="decimal" bind:value={minimum} hint={ingredientText.minimumLimitHint} error={errors.get('minimum')} />
		</div>
		<CheckRow label={ingredientText.indirect} hint={ingredientText.indirectHint} checked={indirect} onchange={() => (indirect = !indirect)} />
	</FormSection>
	<FormSection icon="photo" title={termText.photo} description={ingredientText.photoHint}>
		<PhotoField label={ingredientText.photo} variant="chooser" current={current?.photo_url ?? null} alt={current?.name ?? ''} bind:file={photo} disabled={busy}>
			{#snippet actions()}
				{#if current?.photo_url && !photo}
					<Button label={ingredientText.discardPhoto} icon="trash" variant="dangerSoft" small compact disabled={busy} onclick={onremovephoto} />
				{/if}
			{/snippet}
		</PhotoField>
	</FormSection>
	{#if error && errors.count === 0}
		<div class="mt-4"><Banner tone="danger" icon="alert-triangle">{error}</Banner></div>
	{/if}

	{#snippet footer()}
		<SaveButton busy={busy} onclick={submit} />
		<CancelButton disabled={busy} onclick={onclose} />
	{/snippet}
</FormPage>
