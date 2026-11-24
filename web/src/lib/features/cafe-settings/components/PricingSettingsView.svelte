<script lang="ts">
	import Button from '$lib/components/button/Button.svelte';
	import Banner from '$lib/components/card/Banner.svelte';
	import Card from '$lib/components/card/Card.svelte';
	import CardHeader from '$lib/components/card/CardHeader.svelte';
	import TextField from '$lib/components/form/TextField.svelte';
	import { numberInput, parseNumber } from '$lib/format/number';
	import { actionText } from '$lib/text/actions';
	import { cafeSettingsText as text } from '$lib/text/cafe-settings';
	import { format } from '$lib/text/format';
	import type { CafeSettingsState } from '../cafe-settings.svelte';

	let { cafe }: { cafe: CafeSettingsState } = $props();

	const MAX_MARKUP = 500;
	const MAX_PERCENT = 100;

	let markup = $state('');
	let margin = $state('');
	let tax = $state('');
	let service = $state('');
	let problem = $state('');

	// Isian mengikuti pengaturan tersimpan: cabang lain atau simpanan baru mengisinya ulang.
	$effect(() => {
		const row = cafe.settings;
		markup = row ? numberInput(row.cost_markup_percent) : '';
		margin = row?.target_margin_percent != null ? numberInput(row.target_margin_percent) : '';
		tax = row ? numberInput(row.tax_percent) : '';
		service = row ? numberInput(row.service_percent) : '';
	});

	const percent = (value: string) => (value.trim() ? parseNumber(value) : null);

	function submit(): void {
		const markupValue = percent(markup);
		const taxValue = percent(tax);
		const serviceValue = percent(service);
		const marginValue = percent(margin);
		if (markupValue === null || markupValue < 0 || markupValue > MAX_MARKUP) return void (problem = format(text.markupInvalid, { max: MAX_MARKUP }));
		if (taxValue === null || taxValue < 0 || taxValue > MAX_PERCENT) return void (problem = format(text.taxInvalid, { max: MAX_PERCENT }));
		if (serviceValue === null || serviceValue < 0 || serviceValue > MAX_PERCENT) return void (problem = format(text.serviceInvalid, { max: MAX_PERCENT }));
		if (margin.trim() && (marginValue === null || marginValue <= 0 || marginValue >= MAX_PERCENT)) return void (problem = format(text.marginTargetInvalid, { max: MAX_PERCENT }));
		problem = '';
		void cafe.save(
			{
				cost_markup_percent: String(markupValue),
				target_margin_percent: marginValue === null ? null : String(marginValue),
				tax_percent: String(taxValue),
				service_percent: String(serviceValue)
			},
			text.pricesSaved,
			text.pricesSaveFailed
		);
	}
</script>

{#if cafe.notice}
	<Banner tone="success" icon="circle-check">{cafe.notice}</Banner>
{/if}

{#if cafe.settings}
	{#if cafe.actionError}
		<Banner tone="danger" icon="alert-triangle">{cafe.actionError}</Banner>
	{/if}

	<Card>
		<CardHeader title={text.pricesAndMargin} description={text.pricesDefaultsDescription} />
		<div class="mt-4 grid gap-4 tablet:grid-cols-2 laptop:grid-cols-4">
			<TextField label={text.costMarkupPercent} inputmode="decimal" bind:value={markup} hint={text.costMarkupHint} />
			<TextField label={text.marginTargetPercent} inputmode="decimal" bind:value={margin} hint={text.marginTargetHint} />
			<TextField label={text.taxPercent} inputmode="decimal" bind:value={tax} hint={text.zeroMeansUnused} />
			<TextField label={text.servicePercent} inputmode="decimal" bind:value={service} hint={text.zeroMeansUnused} />
		</div>
	</Card>

	{#if problem}<Banner tone="danger" icon="alert-triangle">{problem}</Banner>{/if}
	<div><Button label={cafe.busy ? actionText.saving : text.savePrices} icon="device-floppy" variant="primary" disabled={cafe.busy} onclick={submit} /></div>
{/if}
