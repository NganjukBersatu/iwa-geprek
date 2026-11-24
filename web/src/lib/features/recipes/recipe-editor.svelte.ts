import { access } from '$lib/auth/access.svelte';
import { recipeText } from '$lib/text/recipes';
import { format } from '$lib/text/format';

// Pesan setelah resep tersimpan, sama di setiap layar yang mengubah resep.
export function savedText(title: string, result: { branches: number; copied: readonly unknown[] }): string {
	const copied = result.copied.length > 0 ? `; ${result.copied.length} bahan baru disalin dengan stok 0` : '';
	return result.branches > 1 ? format(recipeText.recipeSavedInBranches, { name: title, count: result.branches, copied: copied }) : format(recipeText.recipeSaved, { name: title });
}

// Hak akses resep yang dipakai layar menu; mengubah resep dikerjakan di halaman resepnya.
export class RecipeEditor {
	get canRead(): boolean {
		return access.opens('recipes');
	}

	get canManage(): boolean {
		return access.allows('manage_recipes');
	}

	get seesCost(): boolean {
		return access.allows('see_recipe_costs');
	}
}
