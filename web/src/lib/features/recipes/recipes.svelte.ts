import { api } from '$lib/api';
import type { Recipe } from '$lib/api/types';
import { Filters } from '$lib/components/filter/filters.svelte';
import { pageSize } from '$lib/components/pager/size.svelte';
import { ManageState } from '../manage/manage.svelte';
import { access } from '$lib/auth/access.svelte';
import { recipeKey } from './recipe-key';
import { branchList } from '$lib/stores/branch';
import { termText } from '$lib/text/terms';
import { recipeText } from '$lib/text/recipes';

const WITH_RECIPE = 'ada';
const WITHOUT_RECIPE = 'belum';

export type RecipeRow = Recipe & { id: string };
export type RecipeQuery = { branch: string | null; search: string | null; recipe: string | null };

/** Recipes are kept per branch: the list shows one branch, or a row per menu per branch while none is picked. */
export class RecipesState extends ManageState<RecipeRow> {
	readonly filters = new Filters(
		[
			{ kind: 'select', key: 'cabang', label: termText.branch, options: [] },
			{
				kind: 'select',
				key: 'resep',
				label: termText.recipe,
				options: [
					{ value: WITH_RECIPE, label: recipeText.hasRecipe },
					{ value: WITHOUT_RECIPE, label: recipeText.noRecipe }
				]
			}
		]
	);

	get seesCost(): boolean {
		return access.allows('see_recipe_costs');
	}

	get query(): RecipeQuery {
		return { branch: this.filters.get('cabang'), search: this.search || null, recipe: this.filters.get('resep') };
	}

	protected async fetch(): Promise<void> {
		const query = this.query;
		const outlets = await branchList();
		this.filters.setOptions('cabang', outlets.map((outlet) => ({ value: outlet.id, label: outlet.name })));
		const page = await api.recipes.list({ search: query.search ?? undefined, recipe: query.recipe ?? undefined, page: this.page, size: pageSize.value });
		this.items = page.items.map((recipe) => ({ ...recipe, id: recipeKey.join(recipe.menu_id, recipe.outlet_id) }));
		this.total = page.total;
	}

	protected label(row: RecipeRow): string {
		return row.menu_name;
	}

}
