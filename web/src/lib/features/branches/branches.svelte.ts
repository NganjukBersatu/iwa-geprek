import { toast } from '$lib/components/feedback/toast.svelte';
import { api } from '$lib/api';
import type { Branch, BranchCreate, BranchUpdate } from '$lib/api/types';
import { ListSort, sortKeys } from '$lib/components/table/list-sort.svelte';
import { ManageState } from '../manage/manage.svelte';
import { branchColumns } from './columns';


export class BranchesState extends ManageState<Branch> {
	override readonly tables = ['outlets'];
	readonly sort = new ListSort('cabang', sortKeys(branchColumns), () => void this.queryChanged());

	protected async fetch(): Promise<void> {
		this.items = await api.branches.list(this.sort.param);
		this.total = this.items.length;
	}

	protected label(branch: Branch): string {
		return branch.name;
	}

	private announce(text: string): void {
		toast.show(text);
	}

	closeDialogs(): void {
		this.actionError = '';
	}

}
