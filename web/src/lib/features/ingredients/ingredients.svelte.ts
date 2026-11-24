import { userMessage } from '$lib/api/user-message';
import { api } from '$lib/api';
import type { CatalogEntry, Ingredient, IngredientOptions, IngredientUpdate } from '$lib/api/types';
import { toast } from '$lib/components/feedback/toast.svelte';
import { Filters } from '$lib/components/filter/filters.svelte';
import { pageSize } from '$lib/components/pager/size.svelte';
import { STOCK_TABLES } from '$lib/live/tables';
import { collectPages } from '../manage/collect';
import { ManageState } from '../manage/manage.svelte';
import { branchList } from '$lib/stores/branch';
import { ListSort, sortKeys } from '$lib/components/table/list-sort.svelte';
import { ingredientColumns } from './columns';
import { termText } from '$lib/text/terms';
import { ingredientText } from '$lib/text/ingredients';
import { format } from '$lib/text/format';

export type IngredientQuery = { search: string | null; branch: string | null };

export class IngredientsState extends ManageState<Ingredient> {
	override readonly tables = STOCK_TABLES;
	readonly sort = new ListSort('bahan', sortKeys(ingredientColumns), () => void this.queryChanged());

	readonly filters = new Filters([
		{ kind: 'select', key: 'cabang', label: termText.branch, options: [] }
	]);

	outlets = $state<{ id: string; name: string }[]>([]);
	options = $state<IngredientOptions>({ categories: [], units: [] });
	unlinked = $state(0);
	catalog = $state<CatalogEntry[]>([]);
	catalogOpen = $state(false);
	changeOpen = $state(false);
	bulkRemoveOpen = $state(false);

	/** Daftar Bahan memuat yang dipotong resep dan Bahan Tidak Langsung sisanya, jadi satu bahan tidak muncul di dua daftar. */
	constructor(readonly indirect: boolean = false) {
		super();
	}

	get query(): IngredientQuery {
		return { search: this.search || null, branch: this.filters.get('cabang') };
	}

	branchName = (id: string) => this.outlets.find((outlet) => outlet.id === id)?.name ?? '—';

	private params(page: number, size: number) {
		return { search: this.query.search ?? undefined, sort: this.sort.param, page, size, indirect: this.indirect };
	}

	protected override allRows(): Promise<Ingredient[]> {
		return collectPages((page, size) => api.ingredients.list(this.params(page, size)));
	}

	protected async fetch(): Promise<void> {
		const query = this.query;
		const [page, outlets, options] = await Promise.all([api.ingredients.list(this.params(this.page, pageSize.value)), branchList(), api.ingredients.options()]);
		this.items = page.items;
		this.total = page.total;
		this.unlinked = page.unlinked;
		this.outlets = outlets;
		this.options = options;
		this.filters.setOptions('cabang', outlets.map((outlet) => ({ value: outlet.id, label: outlet.name })));
	}

	protected label(ingredient: Ingredient): string {
		return ingredient.name;
	}

	closeDialogs(): void {
		this.catalogOpen = false;
		this.changeOpen = false;
		this.bulkRemoveOpen = false;
		this.actionError = '';
	}

	async openCatalog(): Promise<void> {
		this.actionError = '';
		try {
			this.catalog = await api.ingredients.catalog();
			this.catalogOpen = true;
		} catch (error) {
			this.actionError = userMessage(error, ingredientText.catalogLoadFailed);
		}
	}

	async removeCatalogEntry(entry: CatalogEntry): Promise<void> {
		const done = await this.attempt(() => api.ingredients.removeCatalog(entry.id), ingredientText.catalogRemoveFailed);
		if (!done) return;
		this.catalog = this.catalog.filter((item) => item.id !== entry.id);
		toast.show(format(ingredientText.catalogEntryRemoved, { name: entry.name }));
	}

	async changeSelected(changes: Record<string, string | number | boolean>): Promise<void> {
		await this.bulk('diubah', (ids) => api.ingredients.bulk.update(ids, changes as IngredientUpdate), () => (this.changeOpen = false));
	}

	async removeSelected(): Promise<void> {
		await this.bulk('dihapus', (ids) => api.ingredients.bulk.remove(ids), () => (this.bulkRemoveOpen = false));
	}
}
