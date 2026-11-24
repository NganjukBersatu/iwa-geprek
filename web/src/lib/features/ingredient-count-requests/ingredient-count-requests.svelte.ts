import { api } from '$lib/api';
import type { IngredientCountRequest } from '$lib/api/types';
import { pageSize } from '$lib/components/pager/size.svelte';
import { ManageState } from '../manage/manage.svelte';

/** Pengajuan tutup periode yang menunggu diputus; baris membuka halaman detailnya, tanpa aksi di baris. */
export class IngredientCountRequestsState extends ManageState<IngredientCountRequest> {
	override readonly tables = ['ingredient_count_requests', 'ingredient_counts'];

	protected async fetch(): Promise<void> {
		const page = await api.ingredientCountRequests.list({ page: this.page, size: pageSize.value });
		if (page.items.length === 0 && page.total > 0 && this.page > 1) {
			this.page = Math.ceil(page.total / pageSize.value);
			return this.fetch();
		}
		this.items = page.items;
		this.total = page.total;
	}

	protected label(request: IngredientCountRequest): string {
		return `${request.outlet_name} ${request.close_start}`;
	}
}
