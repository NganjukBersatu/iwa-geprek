<script lang="ts">
	import { controlText } from '$lib/text/controls';
	import { PAGES, extraPath } from '$lib/nav/pages';
	import CancelButton from '$lib/components/button/CancelButton.svelte';
	import SaveButton from '$lib/components/button/SaveButton.svelte';
	import type { Extra, ExtraCategory, ExtraCreate, ExtraUpdate } from '$lib/api/types';
	import Banner from '$lib/components/card/Banner.svelte';
	import FormPage from '$lib/components/form/FormPage.svelte';
	import FormSection from '$lib/components/form/FormSection.svelte';
	import BranchPriceFields from '$lib/components/form/BranchPriceFields.svelte';
	import { BranchPriceForm } from '$lib/components/form/branch-prices.svelte';
	import CheckRow from '$lib/components/form/CheckRow.svelte';
	import MoneyField from '$lib/components/form/MoneyField.svelte';
	import SelectField from '$lib/components/form/SelectField.svelte';
	import TextField from '$lib/components/form/TextField.svelte';
	import { FieldErrors, focusRefused } from '$lib/components/form/field-errors.svelte';
	import { rupiahDigits, rupiahInput } from '$lib/format/currency';
	import { untrack } from 'svelte';
	import { SvelteSet } from 'svelte/reactivity';
	import MenuPicker from '$lib/components/form/MenuPicker.svelte';
	import { termText } from '$lib/text/terms';
	import { actionText } from '$lib/text/actions';
	import { optionText } from '$lib/text/options';
	import { format } from '$lib/text/format';

	let {
		extra,
		menus,
		categories,
		outlets,
		busy,
		error,
		fieldErrors = {},
		onsave,
		onclose
	}: {
		extra: Extra | null;
		menus: { id: string; name: string }[];
		categories: ExtraCategory[];
		outlets: { id: string; name: string }[];
		busy: boolean;
		error: string;
		/** What the server refused, by field name, shown under the field itself. */
		fieldErrors?: Record<string, string>;
		onsave: (body: ExtraCreate | ExtraUpdate) => void;
		onclose: () => void;
	} = $props();

	const NONE = '';
	const current = untrack(() => extra);
	const trail = [
		{ label: PAGES.options.label, href: PAGES.options.path },
		...(current ? [{ label: current.name, href: extraPath(current.id) }, { label: actionText.edit }] : [{ label: optionText.addExtra }])
	];

	let name = $state(current?.name ?? '');
	let price = $state(rupiahInput(current?.price));
	let active = $state(current?.is_active ?? true);
	let categoryId = $state(current?.category_id ?? NONE);
	const branches = new BranchPriceForm(current);
	const chosen = new SvelteSet<string>(current?.menu_ids ?? []);
	const errors = new FieldErrors({ name: optionText.extraName, price: termText.basePrice, category_id: termText.category, outlet_ids: termText.branch }, () => fieldErrors);

	// A refusal from the server puts the cursor in the first refused box.
	$effect(() => {
		if (Object.keys(fieldErrors).length > 0) void focusRefused();
	});

	function submit(): void {
		const found: Record<string, string> = {};
		if (!name.trim()) found.name = optionText.extraNameRequired;
		if (rupiahDigits(price) === '') found.price = optionText.basePriceRequired;
		if (branches.noSeller) found.outlet_ids = optionText.branchRequired;
		if (!errors.check(found)) return;
		onsave({
			name: name.trim(),
			price: rupiahDigits(price),
			is_active: active,
			category_id: categoryId || null,
			outlet_ids: branches.outletIds(),
			branch_prices: branches.branchPrices(outlets),
			menu_ids: [...chosen]
		});
	}
</script>

<FormPage title={current ? format(controlText.editName, { name: current.name }) : optionText.addExtra} description={optionText.extraFormDescription} stacked {trail} {busy} {onclose}>
	<FormSection icon="circle-plus" title={termText.extra} description={optionText.extraSectionDescription}>
		<div class="grid gap-2 tablet:grid-cols-2">
			<TextField label={optionText.extraName} bind:value={name} maxlength={80} required error={errors.get('name')} />
			<MoneyField label={optionText.basePriceRupiah} bind:value={price} required error={errors.get('price')} />
			<SelectField label={termText.category} bind:value={categoryId} options={[{ value: NONE, label: termText.noCategory }, ...categories.map((category) => ({ value: category.id, label: category.name }))]} error={errors.get('category_id')} />
		</div>
		<CheckRow label={termText.active} checked={active} onchange={() => (active = !active)} />
	</FormSection>
	<FormSection icon="building-store" title={optionText.branchesAndPrices} description={optionText.branchesAndPricesDescription}>
		<div class="flex flex-col gap-1" tabindex="-1" aria-invalid={errors.get('outlet_ids') ? true : undefined}>
			<BranchPriceFields form={branches} {outlets} everywhereLabel="Berlaku di semua cabang" hint={optionText.branchPriceHint} />
		</div>
		{#if errors.get('outlet_ids')}<p class="text-xs text-danger-700" role="alert">{errors.get('outlet_ids')}</p>{/if}
	</FormSection>
	<FormSection icon="cup" title={termText.menu} description={optionText.extraMenusDescription}>
		<MenuPicker {menus} {chosen} label={optionText.allowedOnMenus} />
	</FormSection>
	{#if error && errors.count === 0}
		<div class="mt-4"><Banner tone="danger" icon="alert-triangle">{error}</Banner></div>
	{/if}

	{#snippet footer()}
		<SaveButton busy={busy} onclick={submit} />
		<CancelButton disabled={busy} onclick={onclose} />
	{/snippet}
</FormPage>
