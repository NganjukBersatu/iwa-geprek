<script lang="ts">
	import { collectPages } from '../../manage/collect';
	import { controlText } from '$lib/text/controls';
	import { goto } from '$app/navigation';
	import { onMount } from 'svelte';
	import { api } from '$lib/api';
	import type { BulkResult, Ingredient, IngredientTrial, IngredientWaste, WasteCause } from '$lib/api/types';
	import { userMessage } from '$lib/api/user-message';
	import Banner from '$lib/components/card/Banner.svelte';
	import BulkEntryDialog from '$lib/components/dialog/BulkEntryDialog.svelte';
	import type { Field } from '$lib/components/form/types';
	import { PAGES } from '$lib/nav/pages';
	import { TRIAL, WASTE } from '../kinds';
	import { termText } from '$lib/text/terms';
	import { ingredientLossText } from '$lib/text/ingredient-losses';


	let ingredients = $state<Ingredient[]>([]);
	let causes = $state<WasteCause[]>([]);
	let error = $state('');

	onMount(async () => {
		try {
			causes = await api.ingredientMovements.causes();
		} catch (cause) {
			error = userMessage(cause, ingredientLossText.causesLoadFailed);
		}
	});

	/** The ingredients of the branch chosen on the page. */
	async function loadIngredients(outletId: string): Promise<void> {
		ingredients = [];
		if (!outletId) return;
		try {
			ingredients = await collectPages((page, size) => api.ingredients.list({ page, size, outlet_id: outletId }));
		} catch (cause) {
			error = userMessage(cause, controlText.ingredientsLoadFailed);
		}
	}

	/** Waste and trial rows go to their own bulk routes; the answers are put back in the order the rows were typed. */
	async function createMany(rows: Record<string, string | number>[], outletId: string): Promise<BulkResult> {
		const wasteAt: number[] = [];
		const trialAt: number[] = [];
		const wastes: IngredientWaste[] = [];
		const trials: IngredientTrial[] = [];
		rows.forEach((row, index) => {
			const base = { ingredient_id: String(row['ingredient_id']), qty: String(row['qty']), note: row['note'] ? String(row['note']) : null };
			if (row['kind'] === TRIAL) {
				trialAt.push(index);
				trials.push({ ...base, note: String(row['note'] ?? '') });
			} else {
				wasteAt.push(index);
				wastes.push({ ...base, cause: String(row['cause'] ?? '') });
			}
		});
		const [wasteResult, trialResult] = await Promise.all([
			wastes.length ? api.ingredientMovements.wasteBulk.createIn(outletId, wastes) : null,
			trials.length ? api.ingredientMovements.trialBulk.createIn(outletId, trials) : null
		]);
		const results: BulkResult['results'] = [];
		for (const [result, at] of [[wasteResult, wasteAt], [trialResult, trialAt]] as const) {
			result?.results.forEach((outcome, position) => results.push({ ...outcome, row: (at[position] ?? 0) + 1 }));
		}
		results.sort((a, b) => a.row - b.row);
		const succeeded = results.filter((outcome) => outcome.ok).length;
		return { total: results.length, succeeded, failed: results.length - succeeded, results };
	}

	const entryColumns = $derived<Field[]>([
		{ key: 'ingredient_id', label: termText.ingredient, kind: 'select', required: true, options: ingredients.map((item) => ({ value: item.id, label: `${item.name} (${item.unit})` })) },
		{ key: 'kind', label: termText.kind, kind: 'select', required: true, options: [{ value: WASTE, label: termText.damaged }, { value: TRIAL, label: 'RnD' }] },
		{ key: 'qty', label: termText.quantity, kind: 'number', required: true },
		{ key: 'cause', label: ingredientLossText.causeDamaged, kind: 'select', options: causes.map((cause) => ({ value: cause.code, label: cause.label })) },
		{ key: 'note', label: ingredientLossText.noteRnd }
	]);
</script>

{#if error}
	<Banner tone="danger" icon="alert-triangle">{error}</Banner>
{/if}
<BulkEntryDialog
	asPage
	title={ingredientLossText.bulkTitle}
	hint={ingredientLossText.bulkHint}
	columns={entryColumns}
	withBranch
	onbranch={(outletId) => void loadIngredients(outletId)}
	submit={createMany}
	submitLabel="Simpan semua"
	onclose={() => void goto(PAGES.ingredientWaste.path)}
/>
