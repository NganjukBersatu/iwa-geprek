<script lang="ts">
	import { page } from '$app/state';
	import { untrack } from 'svelte';
	import { api } from '$lib/api';
	import type { IngredientMovement, IngredientTrial, IngredientUse, IngredientWaste, WasteCause } from '$lib/api/types';
	import { lossPath, PAGES, usagePath } from '$lib/nav/pages';
	import { createText } from '$lib/text/record-detail';
	import RecordCreateView from '../../record-detail/components/RecordCreateView.svelte';
	import { RecordCreateState } from '../../record-detail/record-create.svelte';
	import { KIND_PARAM, TRIAL, USE, WASTE } from '../kinds';
	import LossForm from './LossForm.svelte';
	import { ingredientLossText } from '$lib/text/ingredient-losses';

	type LossBody = IngredientWaste | IngredientTrial | IngredientUse;
	type LossSave = { body: LossBody; proof: File | null; outletId: string };

	/** Rute pemakaian mencatat pemakaian manual; rute rusak membaca rusak atau RnD dari alamat. */
	let { usage = false }: { usage?: boolean } = $props();

	const kind = untrack(() => usage) ? USE : page.url.searchParams.get(KIND_PARAM) === TRIAL ? TRIAL : WASTE;

	function record(body: LossBody, outletId: string): Promise<IngredientMovement> {
		switch (kind) {
			case USE:
				return api.ingredientMovements.recordUse(outletId, body as IngredientUse);
			case WASTE:
				return api.ingredientMovements.recordWaste(outletId, body as IngredientWaste);
			default:
				return api.ingredientMovements.recordTrial(outletId, body as IngredientTrial);
		}
	}

	const create = new RecordCreateState<IngredientMovement, LossSave, WasteCause[]>({
		context: () => (kind === USE ? api.ingredientMovements.usageCauses() : api.ingredientMovements.causes()),
		create: async ({ body, proof, outletId }) => {
			const saved = await record(body, outletId);
			return proof ? api.ingredientMovements.uploadProof(saved.id, proof) : saved;
		},
		name: (movement) => movement.ingredient_name,
		message: () => ingredientLossText.recorded,
		after: (movement) => (kind === USE ? usagePath(movement.id) : lossPath(movement.id)),
		text: createText('catatan bahan')
	});
</script>

<RecordCreateView {create} back={kind === USE ? PAGES.indirectUsage : PAGES.ingredientWaste}>
	{#snippet form(props)}
		<LossForm
			movement={null}
			{kind}
			causes={props.context ?? []}
			busy={props.busy}
			error={props.error}
			fieldErrors={props.fieldErrors}
			onsave={(body, proof, outletId) => props.onsave({ body: body as LossBody, proof, outletId })}
			onclose={props.onclose}
		/>
	{/snippet}
</RecordCreateView>
