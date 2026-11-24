import { api } from '$lib/api';
import { userMessage } from '$lib/api/user-message';
import type { OptionRecipeResult, OptionRecipeSave } from '$lib/api/types';
import { savedText } from '../recipes/recipe-editor.svelte';
import { optionText } from '$lib/text/options';

/** Setiap baris membawa nama dan satuan bahannya, supaya tetap terbaca walau bahan itu tidak ada di hasil cari pilihan. */
export type RecipeTargetLine = { ingredient_id: string; ingredient_name: string; unit: string | null; qty: string };
export type RecipeTarget = { kind: 'varian' | 'ekstra'; id: string; title: string; lines: RecipeTargetLine[] };

/** The lines of a recipe as the dialog edits them: the quantity as text. */
export const asLines = (recipe: { ingredient_id: string; ingredient_name: string; unit: string | null; qty: string | number }[]): RecipeTargetLine[] =>
	recipe.map((line) => ({ ingredient_id: line.ingredient_id, ingredient_name: line.ingredient_name, unit: line.unit, qty: String(Number(line.qty)) }));

/** The extra recipe of one variant choice or one extra, edited for one branch at a time. */
export class OptionRecipeEditor {
	recipe = $state<RecipeTarget | null>(null);
	/** The branch the open recipe is edited for; its ingredients and its lines follow it. */
	branch = $state('');
	/** Counts the times the lines were re-read for another branch, so the dialog starts over on them. */
	round = $state(0);
	busy = $state(false);
	error = $state('');

	/** `saved` is told the sentence to show once a recipe is stored, and reloads whatever the page shows. */
	constructor(private readonly saved: (text: string) => Promise<void> | void) {}

	open(target: RecipeTarget): void {
		this.error = '';
		this.branch = '';
		this.recipe = target;
	}

	close(): void {
		this.recipe = null;
		this.error = '';
	}

	/** Membaca baris resep untuk cabang yang dipilih di dialog; bahannya dicari dialog itu sendiri di server. */
	async loadFor(outletId: string): Promise<void> {
		const target = this.recipe;
		if (!target || !outletId) return;
		try {
			const recipe =
				target.kind === 'varian'
					? (await api.options.groupsOf(outletId)).flatMap((group) => group.choices).find((choice) => choice.id === target.id)?.recipe
					: (await api.options.extrasOf(outletId)).find((extra) => extra.id === target.id)?.recipe;
			this.recipe = { ...target, lines: asLines(recipe ?? []) };
			this.round += 1;
		} catch (error) {
			this.error = userMessage(error, optionText.recipeLoadFailed);
		}
	}

	async save(body: OptionRecipeSave): Promise<void> {
		const target = this.recipe;
		if (!target) return;
		this.busy = true;
		this.error = '';
		let result: OptionRecipeResult;
		try {
			result = target.kind === 'varian' ? await api.options.saveChoiceRecipe(this.branch, target.id, body) : await api.options.saveExtraRecipe(this.branch, target.id, body);
		} catch (error) {
			this.error = userMessage(error, optionText.recipeSaveFailed);
			return;
		} finally {
			this.busy = false;
		}
		this.close();
		await this.saved(savedText(target.title, result));
	}
}
