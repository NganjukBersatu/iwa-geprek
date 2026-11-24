<script lang="ts">
	import { controlText } from '$lib/text/controls';
	import { PAGES, menuPath } from '$lib/nav/pages';
	import CancelButton from '$lib/components/button/CancelButton.svelte';
	import SaveButton from '$lib/components/button/SaveButton.svelte';
	import type { MenuCategory, MenuCreate, MenuItem, MenuUpdate } from '$lib/api/types';
	import Banner from '$lib/components/card/Banner.svelte';
	import FormPage from '$lib/components/form/FormPage.svelte';
	import FormSection from '$lib/components/form/FormSection.svelte';
	import BranchPriceFields from '$lib/components/form/BranchPriceFields.svelte';
	import { BranchPriceForm } from '$lib/components/form/branch-prices.svelte';
	import CheckRow from '$lib/components/form/CheckRow.svelte';
	import MoneyField from '$lib/components/form/MoneyField.svelte';
	import PhotoField from '$lib/components/form/PhotoField.svelte';
	import SelectField from '$lib/components/form/SelectField.svelte';
	import TextArea from '$lib/components/form/TextArea.svelte';
	import TextField from '$lib/components/form/TextField.svelte';
	import { FieldErrors, focusRefused } from '$lib/components/form/field-errors.svelte';
	import MenuCategoryMissing from '../../menu-categories/components/MenuCategoryMissing.svelte';
	import { rupiahDigits, rupiahInput } from '$lib/format/currency';
	import { untrack } from 'svelte';
	import { termText } from '$lib/text/terms';
	import { actionText } from '$lib/text/actions';
	import { menuText } from '$lib/text/menu';
	import { format } from '$lib/text/format';

	let {
		item,
		categories,
		outlets,
		busy,
		error,
		fieldErrors = {},
		onsave,
		onclose
	}: {
		item: MenuItem | null;
		categories: MenuCategory[];
		outlets: { id: string; name: string }[];
		busy: boolean;
		error: string;
		/** What the server refused, by field name, shown under the field itself. */
		fieldErrors?: Record<string, string>;
		onsave: (body: MenuCreate | MenuUpdate, photo: File | null) => void;
		onclose: () => void;
	} = $props();

	const current = untrack(() => item);
	const trail = [
		{ label: PAGES.menu.label, href: PAGES.menu.path },
		...(current?.category_name ? [{ label: current.category_name }] : []),
		...(current ? [{ label: current.name, href: menuPath(current.id) }, { label: actionText.edit }] : [{ label: menuText.addMenu }])
	];
	const whole = (value: unknown) => (value === null || value === undefined ? '' : String(Number(value)));

	let name = $state(current?.name ?? '');
	let price = $state(rupiahInput(current?.price));
	let categoryId = $state(current?.category_id ?? untrack(() => categories[0]?.id ?? ''));
	let description = $state(current?.description ?? '');
	let available = $state(current?.is_available ?? true);
	let tax = $state(whole(current?.tax_percent));
	let service = $state(whole(current?.service_percent));
	const branches = new BranchPriceForm(current);
	let photo = $state<File | null>(null);
	const errors = new FieldErrors(
		{ name: menuText.menuName, category_id: termText.category, description: termText.description, price: termText.basePrice, tax_percent: menuText.tax, service_percent: menuText.service, outlet_ids: menuText.sellingBranches },
		() => fieldErrors
	);

	// A refusal from the server puts the cursor in the first refused box.
	$effect(() => {
		if (Object.keys(fieldErrors).length > 0) void focusRefused();
	});

	/** Null for an empty box, NaN for a value outside 0 to 100. */
	function percent(text: string): number | null {
		const cleaned = text.trim().replace(',', '.');
		if (cleaned === '') return null;
		const value = Number(cleaned);
		return Number.isFinite(value) && value >= 0 && value <= 100 ? value : Number.NaN;
	}

	function submit(): void {
		const found: Record<string, string> = {};
		if (!name.trim()) found.name = menuText.nameRequired;
		if (!categoryId) found.category_id = menuText.categoryRequired;
		if (rupiahDigits(price) === '') found.price = menuText.basePriceRequired;
		const taxValue = percent(tax);
		const serviceValue = percent(service);
		if (Number.isNaN(taxValue)) found.tax_percent = menuText.percentInvalid;
		if (Number.isNaN(serviceValue)) found.service_percent = menuText.percentInvalid;
		if (branches.noSeller) found.outlet_ids = menuText.branchRequired;
		if (!errors.check(found)) return;
		onsave(
			{
				name: name.trim(),
				price: rupiahDigits(price),
				category_id: categoryId,
				description: description.trim() || null,
				is_available: available,
				outlet_ids: branches.outletIds(),
				branch_prices: branches.branchPrices(outlets),
				tax_percent: taxValue === null ? null : String(taxValue),
				service_percent: serviceValue === null ? null : String(serviceValue)
			},
			photo
		);
	}
</script>

<FormPage title={current ? format(controlText.editName, { name: current.name }) : menuText.addMenu} description={menuText.formDescription} stacked {trail} {busy} {onclose}>
	<FormSection icon="cup" title={termText.menu} description={menuText.nameSectionDescription}>
		<div class="grid gap-2 tablet:grid-cols-2">
			<TextField label={menuText.menuName} bind:value={name} maxlength={255} required error={errors.get('name')} />
			<SelectField label={termText.category} bind:value={categoryId} options={categories.map((category) => ({ value: category.id, label: category.name }))} required hint={menuText.categoryHint} error={errors.get('category_id')} />
		</div>
		{#if categories.length === 0}
			<MenuCategoryMissing />
		{/if}
		<TextArea label={termText.description} bind:value={description} rows={2} maxlength={2000} error={errors.get('description')} />
		<CheckRow label={menuText.available} hint={menuText.availableHint} checked={available} onchange={() => (available = !available)} />
	</FormSection>
	<FormSection icon="cash" title={menuText.priceAndTax} description={menuText.priceAndTaxDescription}>
		<div class="grid gap-2 tablet:grid-cols-3">
			<MoneyField label={menuText.basePriceRupiah} bind:value={price} required error={errors.get('price')} />
			<TextField label={menuText.taxPercent} inputmode="decimal" bind:value={tax} error={errors.get('tax_percent')} />
			<TextField label={menuText.servicePercent} inputmode="decimal" bind:value={service} error={errors.get('service_percent')} />
		</div>
	</FormSection>
	<FormSection icon="building-store" title={menuText.sellingBranches} description={menuText.branchesDescription}>
<div class="flex flex-col gap-1" tabindex="-1" aria-invalid={errors.get('outlet_ids') ? true : undefined}>
			<BranchPriceFields
				form={branches}
				{outlets}
				everywhereLabel="Dijual di semua cabang"
				hint={format(menuText.branchPriceHintWithNote, { note: branches.everywhere ? '' : menuText.branchPriceHintNote })}
			/>
		</div>
		{#if errors.get('outlet_ids')}<p class="text-xs text-danger-700" role="alert">{errors.get('outlet_ids')}</p>{/if}
	</FormSection>
	<FormSection icon="photo" title={termText.photo} description={menuText.photoDescription}>
		<PhotoField label={menuText.photo} current={current?.image_url ?? null} alt={format(controlText.photoOf, { name: current?.name ?? 'menu' })} bind:file={photo} disabled={busy} variant="chooser" />
	</FormSection>
	{#if error && errors.count === 0}
		<div class="mt-4"><Banner tone="danger" icon="alert-triangle">{error}</Banner></div>
	{/if}

	{#snippet footer()}
		<SaveButton busy={busy} onclick={submit} />
		<CancelButton disabled={busy} onclick={onclose} />
	{/snippet}
</FormPage>
