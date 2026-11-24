import { toast } from '$lib/components/feedback/toast.svelte';
import { api } from '$lib/api';
import type { CodeGroup, CodeGroupUpdate, ShiftCategory, ShiftCategoryUpdate } from '$lib/api/types';
import { Filters } from '$lib/components/filter/filters.svelte';
import { ListSort, sortKeys } from '$lib/components/table/list-sort.svelte';
import { ManageState } from '../manage/manage.svelte';
import { shiftCodeColumns } from './columns';
import { branchList } from '$lib/stores/branch';
import { termText } from '$lib/text/terms';
import { shiftCodeText } from '$lib/text/shift-codes';
import { format } from '$lib/text/format';

export class ShiftCodesState extends ManageState<CodeGroup> {
	override readonly tables = ['shift_codes'];
	readonly sort = new ListSort('kode-shift', sortKeys(shiftCodeColumns), () => void this.queryChanged());

	readonly filters = new Filters([
		{ kind: 'select', key: 'cabang', label: termText.branch, options: [] }
	]);

	outlets = $state<{ id: string; name: string }[]>([]);
	categories = $state<string[]>([]);
	categorySettings = $state<ShiftCategory[]>([]);
	categoriesOpen = $state(false);
	changeOpen = $state(false);
	bulkRemoveOpen = $state(false);

	/** Kategori yang belum diatur tidak memeriksa apa pun, jadi admin diingatkan untuk melengkapinya. */
	readonly unsetCategories = $derived(this.categorySettings.filter((category) => !category.shift_kind && !category.start_from).length);
	readonly mismatchedCodes = $derived(this.categorySettings.reduce((total, category) => total + category.mismatched, 0));

	/** Filtering is local: the whole list is small and already here. */
	readonly visible = $derived.by(() => {
		const term = this.search.toLowerCase();
		const branch = this.filters.get('cabang');
		return this.items.filter(
			(group) => (!term || `${group.code} ${group.category}`.toLowerCase().includes(term)) && (!branch || group.branches.some((item) => item.id === branch))
		);
	});

	protected async fetch(): Promise<void> {
		// Pengaturan kategori tidak boleh menggagalkan daftar kode, misalnya saat server belum diperbarui.
		const [groups, outlets, categories, settings] = await Promise.all([
			api.shiftCodes.list(this.sort.param),
			branchList(),
			api.shiftCodes.categories(),
			api.shiftCodes.categorySettings().catch((): ShiftCategory[] => [])
		]);
		this.items = groups;
		this.total = groups.length;
		this.outlets = outlets;
		this.categories = categories;
		this.categorySettings = settings;
		this.filters.setOptions('cabang', outlets.map((outlet) => ({ value: outlet.id, label: outlet.name })));
	}

	protected label(group: CodeGroup): string {
		return group.code;
	}

	private announce(text: string): void {
		toast.show(text);
	}

	closeCategories(): void {
		this.categoriesOpen = false;
	}

	/** Menyimpan pengaturan satu kategori lalu memuat ulang daftar, karena nama dan kecocokan kode ikut berubah; galatnya dilempar ke dialog. */
	async saveCategory(id: string, body: ShiftCategoryUpdate): Promise<void> {
		const saved = await api.shiftCodes.updateCategory(id, body);
		this.announce(format(shiftCodeText.categorySaved, { name: saved.name }));
		await this.refresh();
	}

	/** Menghapus kategori yang tidak dipakai kode mana pun; server menolak yang masih dipakai, dan galatnya dilempar ke dialog. */
	async removeCategory(category: ShiftCategory): Promise<void> {
		await api.shiftCodes.removeCategory(category.id);
		this.announce(format(shiftCodeText.categoryRemoved, { name: category.name }));
		await this.refresh();
	}

	closeDialogs(): void {
		this.changeOpen = false;
		this.bulkRemoveOpen = false;
		this.actionError = '';
	}

	async changeSelected(changes: Record<string, string | number | boolean>): Promise<void> {
		await this.bulk('diubah', (ids) => api.shiftCodes.bulk.update(ids, changes as CodeGroupUpdate), () => (this.changeOpen = false));
	}

	async removeSelected(): Promise<void> {
		await this.bulk('dihapus', (ids) => api.shiftCodes.bulk.remove(ids), () => (this.bulkRemoveOpen = false));
	}
}
