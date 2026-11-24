<script lang="ts">
	import { api } from '$lib/api';
	import type { Ingredient, IngredientCreate, IngredientOptions } from '$lib/api/types';
	import { PAGES, ingredientPath } from '$lib/nav/pages';
	import { branchList } from '$lib/stores/branch';
	import { createText } from '$lib/text/record-detail';
	import RecordCreateView from '../../record-detail/components/RecordCreateView.svelte';
	import { RecordCreateState } from '../../record-detail/record-create.svelte';
	import IngredientForm from './IngredientForm.svelte';
	import { ingredientText } from '$lib/text/ingredients';
	import { format } from '$lib/text/format';

	type IngredientContext = { options: IngredientOptions; outlets: { id: string; name: string }[] };
	type IngredientSave = { body: IngredientCreate; photo: File | null; everywhere: boolean; outletId: string };
	/** One save can make the bahan in several branches; `first` is the one the page opens, `skipped` the branches that already had it. */
	type Created = { first: Ingredient | null; count: number; skipped: string[] };

	const create = new RecordCreateState<Created, IngredientSave, IngredientContext>({
		context: async () => {
			const [options, outlets] = await Promise.all([api.ingredients.options(), branchList()]);
			return { options, outlets };
		},
		create: async ({ body, photo, everywhere, outletId }) => {
			if (everywhere) {
				const result = await api.ingredients.createEverywhere(body);
				if (photo) for (const row of result.created) await api.ingredients.uploadPhoto(row.id, photo);
				return { first: null, count: result.created.length, skipped: result.skipped };
			}
			const saved = await api.ingredients.create(outletId, body);
			if (photo) await api.ingredients.uploadPhoto(saved.id, photo);
			return { first: saved, count: 1, skipped: [] };
		},
		name: (created) => created.first?.name ?? '',
		message: (created) => (created.first ? format(ingredientText.ingredientAdded, { name: created.first.name }) : format(ingredientText.ingredientAddedInBranches, { count: created.count, skipped: created.skipped.length ? format(ingredientText.skippedNote, { names: created.skipped.join(', ') }) : '' })),
		after: (created) => (created.first ? ingredientPath(created.first.id) : PAGES.ingredients.path),
		text: createText('bahan')
	});
</script>

<RecordCreateView {create} back={PAGES.ingredients}>
	{#snippet form(props)}
		<IngredientForm
			ingredient={null}
			options={props.context?.options ?? { categories: [], units: [] }}
			canEverywhere={(props.context?.outlets.length ?? 0) > 1}
			busy={props.busy}
			error={props.error}
			fieldErrors={props.fieldErrors}
			onsave={(body, photo, everywhere, outletId) => props.onsave({ body: body as IngredientCreate, photo, everywhere, outletId })}
			onremovephoto={() => undefined}
			onclose={props.onclose}
		/>
	{/snippet}
</RecordCreateView>
