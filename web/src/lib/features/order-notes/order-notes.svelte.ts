import { api } from '$lib/api';
import type { OrderNote } from '$lib/api/types';
import { ListSort, sortKeys } from '$lib/components/table/list-sort.svelte';
import { ManageState } from '../manage/manage.svelte';
import { orderNoteColumns } from './columns';


/** The order notes the tablets pick from, each branch with its own and the old general ones for all: renamed here to fix a typo, removed only while no order carries them. */
export class OrderNotesState extends ManageState<OrderNote> {
	override readonly tables = ['categories'];
	readonly sort = new ListSort('catatan-pesanan', sortKeys(orderNoteColumns), () => void this.queryChanged());

	protected async fetch(): Promise<void> {
		this.items = await api.orderNotes.list(this.sort.param);
		this.total = this.items.length;
	}

	protected label(note: OrderNote): string {
		return note.name;
	}
}
