<script lang="ts">
	import { api } from '$lib/api';
	import type { IngredientMovement, IngredientReceipt } from '$lib/api/types';
	import { PAGES, receiptPath } from '$lib/nav/pages';
	import { createText } from '$lib/text/record-detail';
	import RecordCreateView from '../../record-detail/components/RecordCreateView.svelte';
	import { RecordCreateState } from '../../record-detail/record-create.svelte';
	import ReceiptForm from './ReceiptForm.svelte';
	import { ingredientReceiptText } from '$lib/text/ingredient-receipts';

	type ReceiptSave = { body: IngredientReceipt; proof: File | null; outletId: string };

	const create = new RecordCreateState<IngredientMovement, ReceiptSave>({
		create: async ({ body, proof, outletId }) => {
			const saved = await api.ingredientMovements.receive(outletId, body);
			return proof ? api.ingredientMovements.uploadProof(saved.id, proof) : saved;
		},
		name: (movement) => movement.ingredient_name,
		message: () => ingredientReceiptText.recorded,
		after: (movement) => receiptPath(movement.id),
		text: createText('catatan barang masuk')
	});
</script>

<RecordCreateView {create} back={PAGES.ingredientReceipts}>
	{#snippet form(props)}
		<ReceiptForm movement={null} busy={props.busy} error={props.error} fieldErrors={props.fieldErrors} onsave={(body, proof, outletId) => props.onsave({ body: body as IngredientReceipt, proof, outletId })} onclose={props.onclose} />
	{/snippet}
</RecordCreateView>
