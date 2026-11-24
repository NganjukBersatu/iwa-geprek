<script lang="ts">
	import { controlText } from '$lib/text/controls';
	import { untrack } from 'svelte';
	import type { StockItem, StockSettings } from '$lib/api/types';
	import CancelButton from '$lib/components/button/CancelButton.svelte';
	import SaveButton from '$lib/components/button/SaveButton.svelte';
	import Banner from '$lib/components/card/Banner.svelte';
	import CheckRow from '$lib/components/form/CheckRow.svelte';
	import FormPage from '$lib/components/form/FormPage.svelte';
	import FormSection from '$lib/components/form/FormSection.svelte';
	import SelectField from '$lib/components/form/SelectField.svelte';
	import TextField from '$lib/components/form/TextField.svelte';
	import { PAGES, stockItemPath } from '$lib/nav/pages';
	import { FieldErrors, focusRefused } from '$lib/components/form/field-errors.svelte';
	import { parseNumber } from '$lib/format/number';
	import { termText } from '$lib/text/terms';
	import { actionText } from '$lib/text/actions';
	import { stockItemText } from '$lib/text/stock-items';
	import { format } from '$lib/text/format';

	let {
		item,
		units,
		busy,
		error,
		fieldErrors = {},
		onsave,
		onclose
	}: {
		item: StockItem;
		units: { id: string; name: string }[];
		busy: boolean;
		error: string;
		/** What the server refused, by field name, shown under the field itself. */
		fieldErrors?: Record<string, string>;
		onsave: (body: StockSettings) => void;
		onclose: () => void;
	} = $props();

	const current = untrack(() => item);
	const trail = [
		{ label: PAGES.stockItems.label, href: PAGES.stockItems.path },
		{ label: current.menu_item_name, href: stockItemPath(current.id) },
		{ label: actionText.edit }
	];

	let unit = $state(current.unit_id ?? '');
	let minimum = $state(String(Number(current.minimum)));
	let tracked = $state(current.is_tracked);
	const errors = new FieldErrors({ unit_id: termText.unit, minimum: stockItemText.minimumLimit }, () => fieldErrors);

	// A refusal from the server puts the cursor in the first refused box.
	$effect(() => {
		if (Object.keys(fieldErrors).length > 0) void focusRefused();
	});

	function submit(): void {
		const found: Record<string, string> = {};
		const least = parseNumber(minimum || '0');
		if (least === null || least < 0) found.minimum = stockItemText.minimumInvalid;
		if (!errors.check(found)) return;
		if (least === null) return;
		onsave({ unit_id: unit || undefined, minimum: String(least), is_tracked: tracked });
	}
</script>

<FormPage title={format(controlText.editName, { name: current.menu_item_name })} description={stockItemText.formDescription} stacked {trail} {busy} {onclose}>
	<FormSection icon="package" title={stockItemText.settingsTitle} description={format(stockItemText.settingsAppliesIn, { name: current.outlet_name })}>
		<div class="grid gap-2 tablet:grid-cols-2">
			<SelectField label={termText.unit} bind:value={unit} options={units.map((entry) => ({ value: entry.id, label: entry.name }))} empty={termText.notSet} error={errors.get('unit_id')} />
			<TextField label={stockItemText.minimumLimit} inputmode="decimal" bind:value={minimum} hint={stockItemText.minimumLimitHint} error={errors.get('minimum')} />
		</div>
		<div class="mt-3">
			<CheckRow label={stockItemText.trackOnSale} hint={stockItemText.trackOnSaleHint} checked={tracked} onchange={() => (tracked = !tracked)} />
		</div>
	</FormSection>
	{#if error && errors.count === 0}
		<div class="mt-4"><Banner tone="danger" icon="alert-triangle">{error}</Banner></div>
	{/if}

	{#snippet footer()}
		<SaveButton {busy} onclick={submit} />
		<CancelButton disabled={busy} onclick={onclose} />
	{/snippet}
</FormPage>
