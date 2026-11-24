<script lang="ts">
	import CancelButton from '$lib/components/button/CancelButton.svelte';
	import SaveButton from '$lib/components/button/SaveButton.svelte';
	import type { OrderCatalog, OrderCorrection, SessionOrderDetail } from '$lib/api/types';
	import Banner from '$lib/components/card/Banner.svelte';
	import FormPage from '$lib/components/form/FormPage.svelte';
	import FormSection from '$lib/components/form/FormSection.svelte';
	import MoneyField from '$lib/components/form/MoneyField.svelte';
	import SelectField from '$lib/components/form/SelectField.svelte';
	import TextField from '$lib/components/form/TextField.svelte';
	import { FieldErrors, focusRefused } from '$lib/components/form/field-errors.svelte';
	import { formatRupiah, rupiahInput, rupiahValue } from '$lib/format/currency';
	import { PAGES, orderPath, sessionPath } from '$lib/nav/pages';
	import { untrack } from 'svelte';
	import DepositedDayWarning from '../../deposits/components/DepositedDayWarning.svelte';
	import { DayWarning } from '../../deposits/day-warning.svelte';
	import { fromItem, lineTotal, toBody, type EditableLine } from '../order-lines';
	import OrderLinesEditor from './OrderLinesEditor.svelte';
	import { termText } from '$lib/text/terms';
	import { sessionDetailText } from '$lib/text/session-detail';
	import { format } from '$lib/text/format';

	type CatalogPromo = OrderCatalog['promos'][number];

	let {
		order,
		catalog,
		busy,
		error,
		fieldErrors = {},
		onsave,
		onclose
	}: {
		order: SessionOrderDetail;
		catalog: OrderCatalog;
		busy: boolean;
		error: string;
		/** What the server refused, by field name, shown under the field itself. */
		fieldErrors?: Record<string, string>;
		onsave: (body: OrderCorrection) => void;
		onclose: () => void;
	} = $props();

	const original = untrack(() => order);
	const title = format(sessionDetailText.correctOrderTitle, { number: original.receipt_number ?? '' }).trim();
	const trail = [
		{ label: PAGES.sessionHistory.label, href: PAGES.sessionHistory.path },
		{ label: format(sessionDetailText.sessionTitle, { name: original.cashier_username ?? '' }).trim(), href: sessionPath(original.session_id) },
		{ label: format(sessionDetailText.orderTitle, { number: original.receipt_number ?? '' }).trim(), href: orderPath(original.session_id, original.id) },
		{ label: sessionDetailText.correction }
	];
	const warning = new DayWarning();
	void warning.read([{ outlet_id: original.outlet_id, day: original.business_day }]);
	const ORDER_TYPES = [
		{ value: 'free_table', label: sessionDetailText.dineIn },
		{ value: 'take_away', label: sessionDetailText.takeaway }
	];
	const NO_PROMO = '';

	let name = $state(original.customer_name ?? '');
	let table = $state(original.table_no ?? '');
	let orderType = $state(original.order_type);
	let method = $state(original.payment_method ?? '');
	let received = $state(rupiahInput(original.cash_received));
	let promo = $state(original.promo_id ?? NO_PROMO);
	let lines = $state<EditableLine[]>(original.items.map(fromItem));
	const errors = new FieldErrors(
		{
			customer_name: sessionDetailText.customerName,
			order_type: sessionDetailText.orderKind,
			table_no: sessionDetailText.tableNumber,
			payment_method: sessionDetailText.paymentMethod,
			cash_received: sessionDetailText.amountReceived,
			promo_id: termText.promo,
			lines: termText.order
		},
		() => fieldErrors
	);

	// A refusal from the server puts the cursor in the first refused box.
	$effect(() => {
		if (Object.keys(fieldErrors).length > 0) void focusRefused();
	});

	const soldAt = new Map(original.items.filter((item) => item.menu_item_id).map((item) => [item.menu_item_id as string, Number(item.unit_price)]));
	const PROMO_LABEL: Record<CatalogPromo['status'], (name: string) => string> = {
		active: (name) => name,
		ended: (name) => format(sessionDetailText.expiredName, { name: name }),
		deleted: () => sessionDetailText.usedPromoExpired
	};
	const methodOptions = $derived(catalog.methods.map((item) => ({ value: item.code, label: item.status === 'active' ? item.label : format(sessionDetailText.inactiveName, { name: item.label }) })));
	const promoOptions = $derived(catalog.promos.map((item) => ({ value: item.id, label: PROMO_LABEL[item.status](item.name) })));
	const needsAmount = $derived(catalog.methods.find((item) => item.code === method)?.needs_change ?? false);
	const estimate = $derived(lines.reduce((sum, line) => sum + lineTotal(line, catalog.menus.find((menu) => menu.id === line.menu_item_id), soldAt), 0));
	const originalLines = JSON.stringify(original.items.map(fromItem).map((line) => toBody({ ...line, key: '' })));

	function submit(): void {
		const found: Record<string, string> = {};
		if (lines.some((line) => !line.menu_item_id)) found.lines = sessionDetailText.itemMenuRequired;
		if (!errors.check(found)) return;
		const body: OrderCorrection = {
			customer_name: name.trim(),
			table_no: orderType === 'take_away' ? '' : table.trim(),
			order_type: orderType as OrderCorrection['order_type'],
			payment_method: method || undefined,
			remove_promo: false
		};
		if (needsAmount && received.trim() !== '') body.cash_received = String(rupiahValue(received));
		if (JSON.stringify(lines.map(toBody)) !== originalLines) body.lines = lines.map(toBody);
		if (promo === NO_PROMO && original.promo_id) body.remove_promo = true;
		else if (promo !== NO_PROMO && promo !== original.promo_id) body.promo_id = promo;
		onsave(body);
	}
</script>

<FormPage {title} description={sessionDetailText.correctionFormDescription} stacked {trail} {busy} {onclose}>
	<FormSection icon="user" title={termText.customer} description={sessionDetailText.customerSectionDescription}>
		<div class="grid gap-2 tablet:grid-cols-3">
			<TextField label={sessionDetailText.customerName} bind:value={name} maxlength={255} placeholder={sessionDetailText.customerNameHint} error={errors.get('customer_name')} />
			<SelectField label={sessionDetailText.orderKind} options={ORDER_TYPES} bind:value={orderType} error={errors.get('order_type')} />
			<TextField label={sessionDetailText.tableNumber} bind:value={table} maxlength={32} disabled={orderType === 'take_away'} placeholder={sessionDetailText.tableNumberExample} error={errors.get('table_no')} />
		</div>
	</FormSection>
	<FormSection icon="cash" title={termText.payment} description={sessionDetailText.paymentSectionDescription}>
		<div class="grid gap-2 tablet:grid-cols-3">
			<SelectField label={sessionDetailText.paymentMethod} options={methodOptions} bind:value={method} error={errors.get('payment_method')} />
			{#if needsAmount}
				<MoneyField label={sessionDetailText.amountReceivedRupiah} bind:value={received} hint={sessionDetailText.amountReceivedMinimum} error={errors.get('cash_received')} />
			{/if}
			<SelectField label={termText.promo} empty={sessionDetailText.noPromo} options={promoOptions} bind:value={promo} error={errors.get('promo_id')} />
		</div>
	</FormSection>
	<FormSection icon="receipt" title={termText.order} description={sessionDetailText.totalNote}>
		<div class="flex flex-col gap-1" tabindex="-1" aria-invalid={errors.get('lines') ? true : undefined}>
			<OrderLinesEditor bind:lines menus={catalog.menus} {soldAt} />
		</div>
		{#if errors.get('lines')}<p class="text-xs text-danger-700" role="alert">{errors.get('lines')}</p>{/if}
		<p class="flex items-center justify-between gap-3 rounded-lg bg-brand-soft px-4 py-3 text-sm font-semibold text-brand-deep">
			<span>{sessionDetailText.estimatedSubtotal}</span>
			<span class="text-base font-semibold">{formatRupiah(estimate)}</span>
		</p>
	</FormSection>

	<DepositedDayWarning {warning} />

	{#if error && errors.count === 0}
		<div class="mt-4"><Banner tone="danger" icon="alert-triangle">{error}</Banner></div>
	{/if}

	{#snippet footer()}
		<SaveButton label={sessionDetailText.saveCorrection} busy={busy} disabled={warning.checking} onclick={submit} />
		<CancelButton disabled={busy} onclick={onclose} />
	{/snippet}
</FormPage>
