import { toast } from '$lib/components/feedback/toast.svelte';
import { api } from '$lib/api';
import type { Announcement, AnnouncementUpdate, Promo, PromoCreate, PromoUpdate } from '$lib/api/types';
import { pageSize } from '$lib/components/pager/size.svelte';
import { Selection } from '$lib/components/table/selection.svelte';
import { collectPages } from '../manage/collect';
import { ManageState } from '../manage/manage.svelte';
import { ListSort, sortKeys } from '$lib/components/table/list-sort.svelte';
import { announcementColumns, promoColumns } from './columns';
import { branchList } from '$lib/stores/branch';



/** Discount promos are the list the shell manages; cafe announcements sit beside them on the same screen. */
export class PromotionsState extends ManageState<Promo> {
	readonly sort = new ListSort('promo', sortKeys(promoColumns), () => void this.queryChanged());
	readonly announcementSort = new ListSort('pengumuman', sortKeys(announcementColumns), () => {
		this.announcementPage = 1;
		void this.load();
	});
	/** The announcements list has its own selection; the base one belongs to the discount promos. */
	readonly announcementSelection = new Selection();
	announcements = $state<Announcement[]>([]);
	announcementPage = $state(1);
	announcementTotal = $state(0);
	entryOpen = $state(false);
	changePromosOpen = $state(false);
	changeAnnouncementsOpen = $state(false);
	bulkRemovePromos = $state(false);
	bulkRemoveAnnouncements = $state(false);

	protected async fetch(): Promise<void> {
		const size = pageSize.value;
		// Kolom Cabang membaca nama cabang, jadi daftar cabang dimuat lebih dulu.
		await branchList();
		const [promos, announcements] = await Promise.all([
			api.promotions.promos({ page: this.page, size, sort: this.sort.param }),
			api.promotions.announcements({ page: this.announcementPage, size, sort: this.announcementSort.param })
		]);
		// A page emptied by a delete moves back to the last page that still has rows, instead of showing an empty list.
		const promoLast = lastPage(promos.total, size);
		const announcementLast = lastPage(announcements.total, size);
		if (this.page > promoLast || this.announcementPage > announcementLast) {
			this.page = Math.min(this.page, promoLast);
			this.announcementPage = Math.min(this.announcementPage, announcementLast);
			return this.fetch();
		}
		this.items = promos.items;
		this.total = promos.total;
		this.announcements = announcements.items;
		this.announcementTotal = announcements.total;
	}

	protected override allRows(): Promise<Promo[]> {
		return collectPages((page, size) => api.promotions.promos({ page, size, sort: this.sort.param }));
	}

	setAnnouncementPage(page: number): void {
		this.announcementPage = page;
		void this.load();
	}

	protected label(promo: Promo): string {
		return promo.name;
	}

	private announce(text: string): void {
		toast.show(text);
	}

	closeDialogs(): void {
		this.entryOpen = false;
		this.changePromosOpen = false;
		this.changeAnnouncementsOpen = false;
		this.bulkRemovePromos = false;
		this.bulkRemoveAnnouncements = false;
		this.actionError = '';
	}

	/** Promos for chosen menus need the menu picker, so they are added one by one; here only the two kinds that need no menu. */
	async createMany(rows: Record<string, string | number>[]) {
		const items = rows.map((row) => ({
			name: String(row.name),
			description: row.description ? String(row.description) : null,
			kind: String(row.kind),
			discount_type: String(row.discount_type),
			value: String(row.value),
			minimum_spend: row.minimum_spend ? String(row.minimum_spend) : null,
			activation: row.activation ? String(row.activation) : 'otomatis',
			starts_on: String(row.starts_on),
			ends_on: String(row.ends_on),
			is_active: true
		})) as PromoCreate[];
		const result = await api.promotions.promoBulk.create(items);
		await this.load();
		return result;
	}

	async changePromos(changes: Record<string, string | number | boolean>): Promise<void> {
		await this.bulk('diubah', (ids) => api.promotions.promoBulk.update(ids, changes as PromoUpdate), () => (this.changePromosOpen = false));
	}

	async removePromos(): Promise<void> {
		await this.bulk('dihapus', (ids) => api.promotions.promoBulk.remove(ids), () => (this.bulkRemovePromos = false));
	}

	private announcementScope() {
		return { selection: this.announcementSelection, name: (id: string) => this.announcements.find((item) => item.id === id)?.title ?? id };
	}

	async changeAnnouncements(changes: Record<string, string | number | boolean>): Promise<void> {
		await this.bulk('diubah', (ids) => api.promotions.announcementBulk.update(ids, changes as AnnouncementUpdate), () => (this.changeAnnouncementsOpen = false), this.announcementScope());
	}

	async removeAnnouncements(): Promise<void> {
		await this.bulk('dihapus', (ids) => api.promotions.announcementBulk.remove(ids), () => (this.bulkRemoveAnnouncements = false), this.announcementScope());
	}

}

function lastPage(total: number, size: number): number {
	return Math.max(1, Math.ceil(total / size));
}
