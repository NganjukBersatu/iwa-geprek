<script lang="ts">
	import { untrack } from 'svelte';
	import { api } from '$lib/api';
	import type { IngredientMovement, IngredientMovementUpdate } from '$lib/api/types';
	import Card from '$lib/components/card/Card.svelte';
	import FigureList from '$lib/components/card/FigureList.svelte';
	import { formatDate } from '$lib/date/range';
	import { EMPTY_VALUE, formatNumber } from '$lib/format/currency';
	import { formatDateTime } from '$lib/format/datetime';
	import { STOCK_TABLES } from '$lib/live/tables';
	import { PAGES } from '$lib/nav/pages';
	import { recordText } from '$lib/text/record-detail';
	import RecordDetailView from '../../record-detail/components/RecordDetailView.svelte';
	import { RecordDetailState } from '../../record-detail/record-detail.svelte';
	import ReceiptForm from './ReceiptForm.svelte';
	import { termText } from '$lib/text/terms';
	import { ingredientReceiptText } from '$lib/text/ingredient-receipts';
	import { format } from '$lib/text/format';

	type ReceiptSave = { body: IngredientMovementUpdate; proof: File | null };

	let { id }: { id: string } = $props();

	const detail = new RecordDetailState<IngredientMovement, ReceiptSave>(untrack(() => id), {
		load: (movementId) => api.ingredientMovements.detail(movementId),
		update: async (movement, { body, proof }) => {
			const saved = await api.ingredientMovements.update(movement.id, body);
			return proof ? api.ingredientMovements.uploadProof(saved.id, proof) : saved;
		},
		remove: (movement) => api.ingredientMovements.remove(movement.id),
		name: (movement) => movement.ingredient_name,
		text: recordText('catatan barang masuk', PAGES.ingredientReceipts.label)
	});
</script>

<RecordDetailView
	{detail}
	back={PAGES.ingredientReceipts}
	trail={(movement) => [{ label: PAGES.ingredientReceipts.label, href: PAGES.ingredientReceipts.path }, { label: movement.ingredient_name }]}
	tables={STOCK_TABLES}
	title={(movement) => movement.ingredient_name}
	description={(movement) => `${formatNumber(movement.qty)} ${movement.unit} · ${formatDate(movement.business_day)}`}
>
	{#snippet body(movement)}
		<div class="flex flex-col gap-4 tablet:gap-6">
			<Card flush>
				<div class="flex flex-col gap-3 bg-brand-soft p-4">
					<span class="text-xs font-medium text-brand-deep">{ingredientReceiptText.proofPhoto}</span>
					<div class="flex aspect-4/3 w-full max-w-80 items-center justify-center overflow-hidden rounded-lg bg-brand-tint">
						{#if movement.proof_url}
							<a href={movement.proof_url} target="_blank" rel="noopener" class="size-full" aria-label={format(ingredientReceiptText.openProofPhoto, { name: movement.ingredient_name })}>
								<img src={movement.proof_url} alt={format(ingredientReceiptText.proofOf, { name: movement.ingredient_name })} class="size-full object-cover" />
							</a>
						{:else}
							<span class="flex flex-col items-center gap-2 text-xs text-brand-deep">
								<i class="ti ti-photo text-display" aria-hidden="true"></i>
								{ingredientReceiptText.noProofPhoto}
							</span>
						{/if}
					</div>
				</div>
			</Card>
			<Card class="flex flex-col gap-5">
				<div class="grid gap-5 tablet:grid-cols-2">
					<FigureList
						title={ingredientReceiptText.receipt}
						figures={[
							{ label: termText.ingredient, value: movement.ingredient_name },
							{ label: termText.quantity, value: `${formatNumber(movement.qty)} ${movement.unit}` }
						]}
					/>
					<FigureList
						title={termText.recording}
						figures={[
							{ label: termText.day, value: formatDate(movement.business_day) },
							{ label: termText.recordedAt, value: formatDateTime(movement.created_at) },
							{ label: termText.recordedByPerson, value: movement.user_name ?? EMPTY_VALUE }
						]}
					/>
				</div>
				<section class="flex flex-col gap-1 border-t border-slate-100 pt-4 text-xs">
					<h3 class="font-semibold text-slate-600">{termText.note}</h3>
					<p class="whitespace-pre-line {movement.note ? 'text-slate-700' : 'text-slate-500'}">{movement.note ?? termText.noNote}</p>
				</section>
			</Card>
		</div>
	{/snippet}
	{#snippet form(props)}
		<ReceiptForm movement={props.record} busy={props.busy} error={props.error} fieldErrors={props.fieldErrors} onsave={(body, proof) => props.onsave({ body: body as IngredientMovementUpdate, proof })} onclose={props.onclose} />
	{/snippet}
	{#snippet removeNote()}
		{ingredientReceiptText.removeNote}
	{/snippet}
</RecordDetailView>
