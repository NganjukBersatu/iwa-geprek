import { toast } from '$lib/components/feedback/toast.svelte';
import { api } from '$lib/api';
import type { SopDraftSummary, SopSummary } from '$lib/api/types';
import { getUser } from '$lib/auth/session';
import { ListSort, sortKeys } from '$lib/components/table/list-sort.svelte';
import { ManageState } from '../manage/manage.svelte';
import { sopColumns } from './columns';
import { sopText } from '$lib/text/sop';


export class SopState extends ManageState<SopSummary> {
	override readonly tables = ['sop', 'sop_slide'];
	readonly sort = new ListSort('sop', sortKeys(sopColumns), () => void this.queryChanged());

	/** Drafts of procedures not saved yet; drafts of existing ones show as a mark on their row. */
	drafts = $state<SopDraftSummary[]>([]);
	ordering = $state(false);
	order = $state<SopSummary[]>([]);
	readonly canOrder = !getUser()?.outlet_id;

	protected async fetch(): Promise<void> {
		const [items, drafts] = await Promise.all([api.sop.list(this.sort.param), api.sop.drafts()]);
		this.items = items;
		this.total = items.length;
		this.drafts = drafts.filter((draft) => draft.sop_id === null);
	}

	protected label(sop: SopSummary): string {
		return sop.title;
	}

	private announce(text: string): void {
		toast.show(text);
	}

	/** Arranging always starts from the order employees read, never from a column order picked for the table. */
	async startOrdering(): Promise<void> {
		const done = await this.attempt(async () => {
			this.order = await api.sop.list();
		}, sopText.orderLoadFailed);
		if (done) this.ordering = true;
	}

	cancelOrdering(): void {
		this.ordering = false;
		this.order = [];
	}

	async saveOrder(): Promise<void> {
		const ids = this.order.map((sop) => sop.id);
		const done = await this.attempt(() => api.sop.reorder(ids), sopText.orderSaveFailed);
		if (!done) return;
		this.ordering = false;
		await this.load();
		this.announce(sopText.orderSaved);
	}
}
