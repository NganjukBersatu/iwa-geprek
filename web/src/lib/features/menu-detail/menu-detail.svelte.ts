import { toast } from '$lib/components/feedback/toast.svelte';
import { ApiError } from '$lib/api/http';
import { userMessage } from '$lib/api/user-message';
import { api } from '$lib/api';
import type { FixedCost, FixedCostUpdate, MenuCategory, MenuCreate, MenuItem, MenuUpdate, Recipe } from '$lib/api/types';
import { access } from '$lib/auth/access.svelte';
import { sellingOutlets, type BranchOption } from '$lib/components/form/branch-prices.svelte';
import { saveMenu } from '../menu/save';
import { RecipeEditor } from '../recipes/recipe-editor.svelte';
import { branchList } from '$lib/stores/branch';
import { menuDetailText } from '$lib/text/menu-detail';
import { format } from '$lib/text/format';


/** One menu: its data, its price per branch, and the recipe of the branch being looked at. */
export class MenuDetailState {
	item = $state<MenuItem | null>(null);
	categories = $state<MenuCategory[]>([]);
	outlets = $state<BranchOption[]>([]);
	loading = $state(true);
	error = $state('');
	busy = $state(false);
	actionError = $state('');
	/** What the server refused about the form, by field name, shown under each field. */
	fieldErrors = $state<Record<string, string>>({});
	removing = $state(false);
	fixedCost = $state<FixedCost | null>(null);
	fixedCostError = $state('');
	fixedCostEditing = $state(false);
	fixedCostClearing = $state(false);
	recipeBranch = $state('');
	recipe = $state<Recipe | null>(null);
	recipeLoading = $state(false);
	recipeError = $state('');
	readonly recipes = new RecipeEditor();
	private token = 0;
	private recipeToken = 0;

	constructor(readonly id: string) {}

	get sellers(): BranchOption[] {
		return this.item ? sellingOutlets(this.item, this.outlets) : [];
	}

	/** Reloads without dimming the screen: what is shown stays until the fresh data arrives. */
	refresh(): Promise<void> {
		return this.load(true);
	}

	async load(quiet = false): Promise<void> {
		const token = ++this.token;
		if (!quiet) this.loading = true;
		try {
			const [item, categories, outlets] = await Promise.all([api.menu.detail(this.id), api.menu.categories(), branchList()]);
			if (token !== this.token) return;
			this.item = item;
			this.categories = categories;
			this.outlets = outlets.map((outlet) => ({ id: outlet.id, name: outlet.name }));
			this.error = '';
		} catch (error) {
			if (token !== this.token) return;
			if (!quiet) {
				this.item = null;
				this.error = userMessage(error, menuDetailText.loadFailed);
			}
		} finally {
			if (token === this.token) this.loading = false;
		}
		await this.loadFixedCost();
		if (!this.recipes.canRead) return;
		const branches = this.sellers;
		if (!branches.some((branch) => branch.id === this.recipeBranch)) this.recipeBranch = branches[0]?.id ?? '';
		await this.loadRecipe(quiet);
	}

	/** Whether the amounts of the fixed cost may be shown and changed; the server refuses them otherwise. */
	get seesFixedCost(): boolean {
		return access.allows('see_recipe_costs');
	}

	async loadFixedCost(): Promise<void> {
		if (!this.item?.has_fixed_cost || !this.seesFixedCost) {
			this.fixedCost = null;
			this.fixedCostError = '';
			return;
		}
		try {
			this.fixedCost = await api.menu.fixedCost.of(this.id);
			this.fixedCostError = '';
		} catch (error) {
			this.fixedCostError = userMessage(error, menuDetailText.fixedCost.loadFailed);
		}
	}

	setRecipeBranch(id: string): void {
		this.recipeBranch = id;
		void this.loadRecipe();
	}

	async loadRecipe(quiet = false): Promise<void> {
		const token = ++this.recipeToken;
		const branch = this.recipeBranch;
		if (!branch) {
			this.recipe = null;
			return;
		}
		if (!quiet) {
			this.recipeLoading = true;
			this.recipe = null;
		}
		try {
			const recipe = await api.recipes.of(branch, this.id);
			if (token !== this.recipeToken) return;
			this.recipe = recipe;
			this.recipeError = '';
		} catch (error) {
			if (token !== this.recipeToken) return;
			this.recipeError = userMessage(error, menuDetailText.recipeLoadFailed);
		} finally {
			if (token === this.recipeToken) this.recipeLoading = false;
		}
	}

	private announce(text: string): void {
		toast.show(text);
	}

	private async attempt(work: () => Promise<unknown>, fallback: string): Promise<boolean> {
		this.busy = true;
		this.actionError = '';
		this.fieldErrors = {};
		try {
			await work();
			return true;
		} catch (error) {
			this.fieldErrors = error instanceof ApiError ? error.fieldErrors : {};
			this.actionError = userMessage(error, fallback);
			return false;
		} finally {
			this.busy = false;
		}
	}

	askRemove(): void {
		this.actionError = '';
		this.removing = true;
	}

	closeDialogs(): void {
		this.removing = false;
		this.fixedCostEditing = false;
		this.fixedCostClearing = false;
		this.actionError = '';
	}

	openFixedCost(): void {
		this.actionError = '';
		this.fixedCostEditing = true;
	}

	askClearFixedCost(): void {
		this.actionError = '';
		this.fixedCostClearing = true;
	}

	async saveFixedCost(body: FixedCostUpdate): Promise<void> {
		if (!(await this.attempt(() => api.menu.fixedCost.save(this.id, body), menuDetailText.fixedCost.saveFailed))) return;
		this.fixedCostEditing = false;
		this.announce(menuDetailText.fixedCost.saved);
		await this.load(true);
	}

	async confirmClearFixedCost(): Promise<void> {
		if (!(await this.attempt(() => api.menu.fixedCost.clear(this.id), menuDetailText.fixedCost.clearFailed))) return;
		this.fixedCostClearing = false;
		this.announce(menuDetailText.fixedCost.cleared);
		await this.load(true);
	}

	async setAvailable(available: boolean): Promise<void> {
		await this.attempt(async () => (this.item = await api.menu.update(this.id, { is_available: available })), menuDetailText.availabilityFailed);
	}

	/** True when the menu was saved, so the edit page returns to it. */
	async save(body: MenuCreate | MenuUpdate, photo: File | null): Promise<boolean> {
		const item = this.item;
		if (!item) return false;
		if (!(await this.attempt(async () => (this.item = await saveMenu(item, body, photo)), menuDetailText.saveFailed))) return false;
		this.announce(format(menuDetailText.nameSaved, { name: this.item?.name ?? item.name }));
		return true;
	}

	/** True when the menu was deleted, so the page returns to the list. */
	async remove(): Promise<boolean> {
		return this.attempt(() => api.menu.remove(this.id), menuDetailText.removeFailed);
	}
}
