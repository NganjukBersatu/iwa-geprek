<script lang="ts">
	import { controlText } from '$lib/text/controls';
	import { PAGES, promoPath } from '$lib/nav/pages';
	import CancelButton from '$lib/components/button/CancelButton.svelte';
	import SaveButton from '$lib/components/button/SaveButton.svelte';
	import { rupiahDigits } from '$lib/format/currency';
	import type { Promo, PromoCreate, PromoUpdate } from '$lib/api/types';
	import Banner from '$lib/components/card/Banner.svelte';
	import FormPage from '$lib/components/form/FormPage.svelte';
	import FormSection from '$lib/components/form/FormSection.svelte';
	import CheckRow from '$lib/components/form/CheckRow.svelte';
	import MenuPicker from '$lib/components/form/MenuPicker.svelte';
	import MoneyField from '$lib/components/form/MoneyField.svelte';
	import SelectField from '$lib/components/form/SelectField.svelte';
	import ScopeField from '$lib/components/form/ScopeField.svelte';
	import { branches } from '$lib/stores/branch';
	import TextArea from '$lib/components/form/TextArea.svelte';
	import TextField from '$lib/components/form/TextField.svelte';
	import { FieldErrors, focusRefused } from '$lib/components/form/field-errors.svelte';
	import { todayIso } from '$lib/date/range';
	import { untrack } from 'svelte';
	import { SvelteSet } from 'svelte/reactivity';
	import { KIND_LABELS } from '../labels';
	import { termText } from '$lib/text/terms';
	import { actionText } from '$lib/text/actions';
	import { promotionText } from '$lib/text/promotions';
	import { format } from '$lib/text/format';

	let {
		promo,
		menus,
		busy,
		error,
		fieldErrors = {},
		onsave,
		onclose
	}: {
		promo: Promo | null;
		menus: { id: string; name: string }[];
		busy: boolean;
		error: string;
		/** What the server refused, by field name, shown under the field itself. */
		fieldErrors?: Record<string, string>;
		onsave: (body: PromoCreate | PromoUpdate) => void;
		onclose: () => void;
	} = $props();

	type Kind = PromoCreate['kind'];
	type DiscountType = PromoCreate['discount_type'];
	type Activation = NonNullable<PromoCreate['activation']>;

	const current = untrack(() => promo);
	const trail = [
		{ label: PAGES.promotions.label, href: PAGES.promotions.path },
		...(current ? [{ label: current.name, href: promoPath(current.id) }, { label: actionText.edit }] : [{ label: promotionText.addPromo }])
	];
	const whole = (value: string | number | null | undefined) => (value === null || value === undefined ? '' : String(Number(value)));

	let name = $state(current?.name ?? '');
	let scope = $state(current?.outlet_id ?? '');
	let description = $state(current?.description ?? '');
	let kind = $state<string>(current?.kind ?? 'basic');
	let discountType = $state<string>(current?.discount_type ?? 'persen');
	let percent = $state(current?.discount_type === 'persen' ? whole(current.value) : '');
	let nominal = $state(current?.discount_type === 'nominal' ? whole(current.value) : '');
	let minimum = $state(whole(current?.minimum_spend));
	let activation = $state<string>(current?.activation ?? 'otomatis');
	let startsOn = $state(current?.starts_on ?? todayIso());
	let endsOn = $state(current?.ends_on ?? todayIso());
	let active = $state(current?.is_active ?? true);
	const chosen = new SvelteSet<string>(current?.product_ids ?? []);
	const errors = new FieldErrors(
		{
			name: promotionText.promoName,
			kind: promotionText.appliesTo,
			discount_type: promotionText.discountType,
			value: termText.discount,
			minimum_spend: promotionText.minimumPurchase,
			activation: promotionText.activation,
			description: termText.description,
			starts_on: promotionText.startDate,
			ends_on: promotionText.endDate,
			product_ids: termText.menu
		},
		() => fieldErrors
	);

	// A refusal from the server puts the cursor in the first refused box.
	$effect(() => {
		if (Object.keys(fieldErrors).length > 0) void focusRefused();
	});

	const kindOptions = Object.entries(KIND_LABELS).map(([value, label]) => ({ value, label }));
	const typeOptions = [
		{ value: 'persen', label: promotionText.percent },
		{ value: 'nominal', label: promotionText.amount }
	];
	const activationOptions = [
		{ value: 'otomatis', label: promotionText.automaticAtCashier },
		{ value: 'manual', label: promotionText.chosenByCashier }
	];

	function value(): string | null {
		if (discountType === 'nominal') {
			const typed = rupiahDigits(nominal);
			return typed && Number(typed) > 0 ? typed : null;
		}
		const typed = Number(percent.trim().replace(',', '.'));
		return Number.isFinite(typed) && typed > 0 && typed <= 100 ? String(typed) : null;
	}

	function submit(): void {
		const found: Record<string, string> = {};
		const amount = value();
		if (!name.trim()) found.name = promotionText.promoNameRequired;
		if (amount === null) found.value = discountType === 'persen' ? promotionText.percentInvalid : promotionText.amountInvalid;
		if (kind === 'total' && !(Number(rupiahDigits(minimum)) > 0)) found.minimum_spend = promotionText.minimumPurchaseRequired;
		if (!startsOn) found.starts_on = promotionText.promoStartRequired;
		if (!endsOn) found.ends_on = promotionText.promoEndRequired;
		else if (startsOn && endsOn < startsOn) found.ends_on = promotionText.endBeforeStart;
		if (kind === 'produk' && chosen.size === 0) found.product_ids = promotionText.menuRequired;
		if (!errors.check(found)) return;
		if (amount === null) return;
		onsave({
			name: name.trim(),
			description: description.trim() || null,
			kind: kind as Kind,
			discount_type: discountType as DiscountType,
			value: amount,
			product_ids: kind === 'produk' ? [...chosen] : null,
			minimum_spend: kind === 'total' ? rupiahDigits(minimum) : null,
			activation: activation as Activation,
			starts_on: startsOn,
			ends_on: endsOn,
			is_active: active,
			outlet_id: scope || null
		});
	}
</script>

<FormPage title={current ? format(controlText.editName, { name: current.name }) : promotionText.addPromo} description={promotionText.promoFormDescription} stacked {trail} {busy} {onclose}>
	<FormSection icon="discount-2" title={termText.promo} description={promotionText.promoSectionDescription}>
		<div class="grid gap-3 tablet:grid-cols-2">
			<TextField label={promotionText.promoName} bind:value={name} maxlength={255} required error={errors.get('name')} />
			<SelectField label={promotionText.appliesTo} bind:value={kind} options={kindOptions} error={errors.get('kind')} />
			<SelectField label={promotionText.discountType} bind:value={discountType} options={typeOptions} error={errors.get('discount_type')} />
			{#if discountType === 'persen'}
				<TextField label={promotionText.discountPercent} inputmode="decimal" bind:value={percent} required error={errors.get('value')} />
			{:else}
				<MoneyField label={promotionText.discountAmount} bind:value={nominal} required error={errors.get('value')} />
			{/if}
			{#if kind === 'total'}
				<MoneyField label={promotionText.minimumPurchaseAmount} bind:value={minimum} required error={errors.get('minimum_spend')} />
			{/if}
			<SelectField label={promotionText.activation} bind:value={activation} options={activationOptions} error={errors.get('activation')} />
			<ScopeField bind:value={scope} outlets={$branches} hint={promotionText.promoScopeHint} />
		</div>
		<TextArea label={termText.description} bind:value={description} maxlength={2000} rows={3} error={errors.get('description')} />
	</FormSection>
	<FormSection icon="calendar-event" title={promotionText.validity} description={promotionText.validityHint}>
		<div class="grid gap-3 tablet:grid-cols-2">
			<TextField label={promotionText.startDate} type="date" bind:value={startsOn} required error={errors.get('starts_on')} />
			<TextField label={promotionText.endDate} type="date" bind:value={endsOn} required error={errors.get('ends_on')} />
		</div>
		<CheckRow label={termText.active} checked={active} onchange={() => (active = !active)} />
	</FormSection>
	{#if kind === 'produk'}
		<FormSection icon="cup" title={termText.menu} description={promotionText.menusSectionDescription}>
			<div class="flex flex-col gap-1" tabindex="-1" aria-invalid={errors.get('product_ids') ? true : undefined}>
				<MenuPicker {menus} {chosen} label={promotionText.discountedMenus} />
			</div>
			{#if errors.get('product_ids')}<p class="text-xs text-danger-700" role="alert">{errors.get('product_ids')}</p>{/if}
		</FormSection>
	{/if}
	{#if error && errors.count === 0}
		<div class="mt-4"><Banner tone="danger" icon="alert-triangle">{error}</Banner></div>
	{/if}

	{#snippet footer()}
		<SaveButton busy={busy} onclick={submit} />
		<CancelButton disabled={busy} onclick={onclose} />
	{/snippet}
</FormPage>
