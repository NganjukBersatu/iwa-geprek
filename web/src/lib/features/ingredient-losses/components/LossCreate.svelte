<script lang="ts">
	import { page } from '$app/state';
	import { api } from '$lib/api';
	import type { IngredientMovement, IngredientTrial, IngredientWaste, WasteCause } from '$lib/api/types';
	import { lossPath, PAGES } from '$lib/nav/pages';
	import { createText } from '$lib/text/record-detail';
	import RecordCreateView from '../../record-detail/components/RecordCreateView.svelte';
	import { RecordCreateState } from '../../record-detail/record-create.svelte';
	import { KIND_PARAM, TRIAL, WASTE } from '../kinds';
	import LossForm from './LossForm.svelte';
	import { ingredientLossText } from '$lib/text/ingredient-losses';

	type LossSave = { body: IngredientWaste | IngredientTrial; proof: File | null; outletId: string };

	const kind = page.url.searchParams.get(KIND_PARAM) === TRIAL ? TRIAL : WASTE;

	const create = new RecordCreateState<IngredientMovement, LossSave, WasteCause[]>({
		context: () => api.ingredientMovements.causes(),
		create: async ({ body, proof, outletId }) => {
			const saved =
				kind === WASTE
					? await api.ingredientMovements.recordWaste(outletId, body as IngredientWaste)
					: await api.ingredientMovements.recordTrial(outletId, body as IngredientTrial);
			return proof ? api.ingredientMovements.uploadProof(saved.id, proof) : saved;
		},
		name: (movement) => movement.ingredient_name,
		message: () => ingredientLossText.recorded,
		after: (movement) => lossPath(movement.id),
		text: createText('catatan bahan')
	});
</script>

<RecordCreateView {create} back={PAGES.ingredientWaste}>
	{#snippet form(props)}
		<LossForm
			movement={null}
			{kind}
			causes={props.context ?? []}
			busy={props.busy}
			error={props.error}
			fieldErrors={props.fieldErrors}
			onsave={(body, proof, outletId) => props.onsave({ body: body as IngredientWaste | IngredientTrial, proof, outletId })}
			onclose={props.onclose}
		/>
	{/snippet}
</RecordCreateView>
