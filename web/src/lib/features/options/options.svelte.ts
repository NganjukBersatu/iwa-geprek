import { toast } from '$lib/components/feedback/toast.svelte';
import { api } from '$lib/api';
import type { Extra, ExtraCategory, ExtraCreate, ExtraUpdate, OptionMenu, VariantGroup, VariantGroupCreate, VariantGroupUpdate } from '$lib/api/types';
import { access } from '$lib/auth/access.svelte';
import { Filters } from '$lib/components/filter/filters.svelte';
import { Selection } from '$lib/components/table/selection.svelte';
import { ListSort, sortKeys } from '$lib/components/table/list-sort.svelte';
import { ManageState } from '../manage/manage.svelte';
import { extraColumns, groupColumns } from './columns';
import { branchList } from '$lib/stores/branch';
import { optionText } from '$lib/text/options';


/** Variant groups are the list the shell manages; extras sit beside them on the same screen. */
export class OptionsState extends ManageState<VariantGroup> {
	readonly filters = new Filters([{ kind: 'select', key: 'cabang', label: optionText.recipeBranch, options: [] }]);
	readonly sort = new ListSort('varian-kelompok', sortKeys(groupColumns), () => void this.queryChanged());
	readonly extraSort = new ListSort('ekstra-daftar', sortKeys(extraColumns([])), () => void this.queryChanged());

	get canVariants(): boolean {
		return access.allows('manage_variants');
	}

	get canExtras(): boolean {
		return access.allows('manage_extras');
	}
	/** The extras list has its own selection; the base one belongs to the variant groups. */
	readonly extraSelection = new Selection();
	extras = $state<Extra[]>([]);
	bulkRemoveGroups = $state(false);
	bulkRemoveExtras = $state(false);
	menus = $state<OptionMenu[]>([]);
	categories = $state<ExtraCategory[]>([]);
	outlets = $state<{ id: string; name: string }[]>([]);

	get query(): string | null {
		return this.filters.get('cabang');
	}

	protected async fetch(): Promise<void> {
		this.outlets = await branchList();
		this.filters.setOptions('cabang', this.outlets.map((outlet) => ({ value: outlet.id, label: outlet.name })));
		const [groups, extras, menus, categories] = await Promise.all([
			this.canVariants ? api.options.groups(this.sort.param) : Promise.resolve([]),
			this.canExtras ? api.options.extras(this.extraSort.param) : Promise.resolve([]),
			api.options.menus(),
			this.canExtras ? api.options.categories() : Promise.resolve([])
		]);
		this.items = groups;
		this.total = groups.length;
		this.extras = extras;
		this.menus = menus;
		this.categories = categories;
	}

	protected label(group: VariantGroup): string {
		return group.name;
	}

	private announce(text: string): void {
		toast.show(text);
	}

	closeDialogs(): void {
		this.bulkRemoveGroups = false;
		this.bulkRemoveExtras = false;
		this.actionError = '';
	}

	async removeSelectedGroups(): Promise<void> {
		await this.bulk('dihapus', (ids) => api.options.groupsBulk.remove(ids), () => (this.bulkRemoveGroups = false));
	}

	async removeSelectedExtras(): Promise<void> {
		await this.bulk('dihapus', (ids) => api.options.extrasBulk.remove(ids), () => (this.bulkRemoveExtras = false), {
			selection: this.extraSelection,
			name: (id) => this.extras.find((extra) => extra.id === id)?.name ?? id
		});
	}
}
