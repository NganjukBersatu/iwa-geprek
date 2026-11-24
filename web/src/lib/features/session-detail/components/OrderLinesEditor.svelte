<script lang="ts">
	import type { OrderCatalogMenu } from '$lib/api/types';
	import DeleteButton from '$lib/components/button/DeleteButton.svelte';
	import Button from '$lib/components/button/Button.svelte';
	import CheckRow from '$lib/components/form/CheckRow.svelte';
	import QuantityStepper from '$lib/components/form/QuantityStepper.svelte';
	import SelectField from '$lib/components/form/SelectField.svelte';
	import TextField from '$lib/components/form/TextField.svelte';
	import { formatRupiah } from '$lib/format/currency';
	import { blankLine, lineTotal, type EditableLine } from '../order-lines';
	import { termText } from '$lib/text/terms';
	import { sessionDetailText } from '$lib/text/session-detail';
	import { format } from '$lib/text/format';

	let {
		lines = $bindable(),
		menus,
		soldAt
	}: {
		lines: EditableLine[];
		menus: OrderCatalogMenu[];
		soldAt: Map<string, number>;
	} = $props();

	const menuOptions = $derived(menus.map((menu) => ({ value: menu.id, label: menu.name })));
	const menuOf = (id: string) => menus.find((menu) => menu.id === id);

	function changeMenu(line: EditableLine, id: string): void {
		line.menu_item_id = id;
		line.variant_ids = [];
		line.extras = [];
	}

	function chosenIn(line: EditableLine, groupId: string): string {
		const group = menuOf(line.menu_item_id)?.variant_groups.find((item) => item.id === groupId);
		return group?.choices.find((choice) => line.variant_ids.includes(choice.id))?.id ?? '';
	}

	function chooseVariant(line: EditableLine, groupId: string, choiceId: string): void {
		const group = menuOf(line.menu_item_id)?.variant_groups.find((item) => item.id === groupId);
		const others = line.variant_ids.filter((id) => !group?.choices.some((choice) => choice.id === id));
		line.variant_ids = choiceId ? [...others, choiceId] : others;
	}

	const extraOf = (line: EditableLine, extraId: string) => line.extras.find((pick) => pick.extra_id === extraId);

	function toggleExtra(line: EditableLine, extraId: string): void {
		line.extras = extraOf(line, extraId) ? line.extras.filter((pick) => pick.extra_id !== extraId) : [...line.extras, { extra_id: extraId, qty: 1 }];
	}
</script>

<div class="flex flex-col gap-3">
	{#each lines as line, index (line.key)}
		{@const menu = menuOf(line.menu_item_id)}
		<div class="flex flex-col gap-3 rounded-lg border border-slate-200 bg-slate-50 p-3">
			<div class="grid items-end gap-3 tablet:grid-cols-[1fr_auto_auto]">
				<SelectField label={format(sessionDetailText.menuNumber, { number: index + 1 })} options={menuOptions} bind:value={() => line.menu_item_id, (id) => changeMenu(line, id)} />
				<QuantityStepper label={format(sessionDetailText.quantityOf, { name: menu?.name ?? 'item' })} bind:value={line.qty} />
				<div class="flex items-center justify-between gap-3 tablet:justify-end">
					<span class="text-sm font-semibold text-slate-800">{formatRupiah(lineTotal(line, menu, soldAt))}</span>
					<DeleteButton label={sessionDetailText.removeItem} small disabled={lines.length === 1} onclick={() => (lines = lines.filter((item) => item.key !== line.key))} />
				</div>
			</div>

			{#if menu && menu.variant_groups.length > 0}
				<div class="grid gap-3 tablet:grid-cols-2">
					{#each menu.variant_groups as group (group.id)}
						<SelectField
							label={group.required ? `${group.name} *` : group.name}
							empty={group.required ? undefined : sessionDetailText.noChoice}
							options={group.choices.map((choice) => ({ value: choice.id, label: choice.name }))}
							bind:value={() => chosenIn(line, group.id), (id) => chooseVariant(line, group.id, id)}
						/>
					{/each}
				</div>
			{/if}

			{#if menu && menu.extras.length > 0}
				<fieldset class="flex flex-col gap-1">
					<legend class="text-xs font-semibold text-slate-600">{termText.extra}</legend>
					<div class="grid gap-x-3 tablet:grid-cols-2">
						{#each menu.extras as extra (extra.id)}
							{@const pick = extraOf(line, extra.id)}
							<div class="flex items-center justify-between gap-2">
								<CheckRow label={extra.name} hint={formatRupiah(extra.price)} checked={!!pick} onchange={() => toggleExtra(line, extra.id)} />
								{#if pick}
									<QuantityStepper label={format(sessionDetailText.quantityOf, { name: extra.name })} bind:value={pick.qty} />
								{/if}
							</div>
						{/each}
					</div>
				</fieldset>
			{/if}

			<TextField label={sessionDetailText.itemNote} bind:value={line.note} maxlength={255} placeholder={sessionDetailText.itemNoteExample} />
		</div>
	{/each}
	<Button label={sessionDetailText.addItem} icon="plus" class="self-start" onclick={() => (lines = [...lines, blankLine(menus[0])])} />
</div>
