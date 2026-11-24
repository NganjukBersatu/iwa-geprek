import { api } from '$lib/api';
import type { MenuCategoryRecord } from '$lib/api/types';
import { toast } from '$lib/components/feedback/toast.svelte';
import { ListSort, sortKeys } from '$lib/components/table/list-sort.svelte';
import { ManageState } from '../manage/manage.svelte';
import { menuCategoryColumns } from './columns';
import { menuCategoryText } from '$lib/text/menu-categories';
import { format } from '$lib/text/format';

/** The categories of the menu; a category has one field, so it is added, renamed and removed from dialogs on the list itself. */
export class MenuCategoriesState extends ManageState<MenuCategoryRecord> {
	override readonly tables = ['categories', 'menu_items', 'category_stations', 'stations'];
	readonly sort = new ListSort('kategori-menu', sortKeys(menuCategoryColumns), () => void this.queryChanged());

	/** The category being renamed; empty while a new one is added or no dialog is open. */
	editing = $state<MenuCategoryRecord | null>(null);
	creating = $state(false);
	removing = $state<MenuCategoryRecord | null>(null);

	get formOpen(): boolean {
		return this.creating || this.editing !== null;
	}

	protected async fetch(): Promise<void> {
		this.items = await api.menuCategories.list(this.sort.param);
		this.total = this.items.length;
	}

	protected label(category: MenuCategoryRecord): string {
		return category.name;
	}

	openNew(): void {
		this.closeDialogs();
		this.creating = true;
	}

	openEdit(category: MenuCategoryRecord): void {
		this.closeDialogs();
		this.editing = category;
	}

	/** Removing asks again in a dialog of its own, so the form is closed first and two dialogs never overlap. */
	askRemove(category: MenuCategoryRecord): void {
		this.closeDialogs();
		this.removing = category;
	}

	closeDialogs(): void {
		this.creating = false;
		this.editing = null;
		this.removing = null;
		this.actionError = '';
		this.fieldErrors = {};
	}

	async save(name: string): Promise<void> {
		const target = this.editing;
		const saved = await this.attempt(() => (target ? api.menuCategories.update(target.id, { name }) : api.menuCategories.create({ name })), menuCategoryText.saveFailed);
		if (!saved) return;
		toast.show(target ? format(menuCategoryText.categorySaved, { name: name }) : format(menuCategoryText.categoryAdded, { name: name }));
		this.closeDialogs();
		await this.refresh();
	}

	async remove(): Promise<void> {
		const target = this.removing;
		if (!target) return;
		const removed = await this.attempt(() => api.menuCategories.remove(target.id), menuCategoryText.removeFailed);
		if (!removed) return;
		toast.show(format(menuCategoryText.categoryRemoved, { name: target.name }));
		this.closeDialogs();
		await this.refresh();
	}
}
