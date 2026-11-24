import { toast } from '$lib/components/feedback/toast.svelte';
import { api } from '$lib/api';
import type { MenuCategory, MenuItem, MenuUpdate } from '$lib/api/types';
import { Filters } from '$lib/components/filter/filters.svelte';
import { pageSize } from '$lib/components/pager/size.svelte';
import { collectPages } from '../manage/collect';
import { ManageState } from '../manage/manage.svelte';
import { branchList } from '$lib/stores/branch';
import { ListSort, sortKeys } from '$lib/components/table/list-sort.svelte';
import { menuColumns } from './columns';
import { termText } from '$lib/text/terms';
import { menuText } from '$lib/text/menu';

const AVAILABLE = 'tersedia';
const UNAVAILABLE = 'habis';

export type MenuQuery = { search: string | null; category: string | null; availability: string | null };

export class MenuState extends ManageState<MenuItem> {
	readonly sort = new ListSort('menu', sortKeys(menuColumns([])), () => void this.queryChanged());
	readonly filters = new Filters([
		{ kind: 'select', key: 'kategori', label: termText.category, options: [] },
		{
			kind: 'select',
			key: 'ketersediaan',
			label: menuText.availability,
			options: [
				{ value: AVAILABLE, label: menuText.available },
				{ value: UNAVAILABLE, label: termText.outOfStock }
			]
		}
	]);

	categories = $state<MenuCategory[]>([]);
	outlets = $state<{ id: string; name: string }[]>([]);
	changeOpen = $state(false);
	bulkRemoveOpen = $state(false);

	get query(): MenuQuery {
		return { search: this.search || null, category: this.filters.get('kategori'), availability: this.filters.get('ketersediaan') };
	}

	private params(page: number, size: number) {
		const query = this.query;
		return {
			search: query.search ?? undefined,
			category_id: query.category ?? undefined,
			available: query.availability === AVAILABLE ? true : query.availability === UNAVAILABLE ? false : undefined,
			sort: this.sort.param,
			page,
			size
		};
	}

	protected override allRows(): Promise<MenuItem[]> {
		return collectPages((page, size) => api.menu.list(this.params(page, size)));
	}

	protected async fetch(): Promise<void> {
		const query = this.query;
		const [page, categories, outlets] = await Promise.all([
			api.menu.list(this.params(this.page, pageSize.value)),
			api.menu.categories(),
			branchList()
		]);
		this.items = page.items;
		this.total = page.total;
		this.categories = categories;
		this.outlets = outlets;
		this.filters.setOptions('kategori', categories.map((category) => ({ value: category.id, label: category.name })));
	}

	protected label(item: MenuItem): string {
		return item.name;
	}

	private announce(text: string): void {
		toast.show(text);
	}

	closeDialogs(): void {
		this.changeOpen = false;
		this.bulkRemoveOpen = false;
		this.actionError = '';
	}

	async changeSelected(changes: Record<string, string | number | boolean>): Promise<void> {
		await this.bulk('diubah', (ids) => api.menu.bulk.update(ids, changes as MenuUpdate), () => (this.changeOpen = false));
	}

	async removeSelected(): Promise<void> {
		await this.bulk('dihapus', (ids) => api.menu.bulk.remove(ids), () => (this.bulkRemoveOpen = false));
	}
}
