<script lang="ts">
	import type { CafeSettings } from '$lib/api/types';
	import Button from '$lib/components/button/Button.svelte';
	import Banner from '$lib/components/card/Banner.svelte';
	import Card from '$lib/components/card/Card.svelte';
	import CardHeader from '$lib/components/card/CardHeader.svelte';
	import SelectField from '$lib/components/form/SelectField.svelte';
	import { actionText } from '$lib/text/actions';
	import { cafeSettingsText as text } from '$lib/text/cafe-settings';
	import type { CafeSettingsState } from '../cafe-settings.svelte';

	type OrderType = CafeSettings['default_order_type'];

	let { cafe }: { cafe: CafeSettingsState } = $props();

	const ORDER_TYPES: OrderType[] = ['free_table', 'take_away'];
	const options = ORDER_TYPES.map((value) => ({ value, label: text.orderTypes[value] }));

	let orderType = $state<string>('free_table');

	// Isian mengikuti pengaturan tersimpan: cabang lain atau simpanan baru mengisinya ulang.
	$effect(() => {
		orderType = cafe.settings?.default_order_type ?? 'free_table';
	});

	function chosen(value: string): OrderType {
		return ORDER_TYPES.find((type) => type === value) ?? 'free_table';
	}

	function submit(): void {
		void cafe.save({ default_order_type: chosen(orderType) }, text.cashierSaved, text.cashierSaveFailed);
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
		<CardHeader title={text.cashierSettings} description={text.cashierSettingsDescription} />
		<div class="mt-4 grid gap-4 tablet:grid-cols-2">
			<SelectField label={text.defaultOrderType} bind:value={orderType} {options} hint={text.defaultOrderTypeHint} />
		</div>
	</Card>

	<div><Button label={cafe.busy ? actionText.saving : text.saveCashier} icon="device-floppy" variant="primary" disabled={cafe.busy} onclick={submit} /></div>
{/if}
