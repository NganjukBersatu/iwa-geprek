import { bulkApi } from './bulk';
import { del, patch, post, request, toQuery, upload, type SortParam } from './http';
import type { Announcement, AnnouncementCreate, AnnouncementPage, AnnouncementUpdate, Promo, PromoCreate, PromoMenu, PromoPage, PromoUpdate } from './types';

const BASE = '/web/management/promotions';

export type PromotionPageParams = SortParam & { page: number; size: number };

export const promotionsApi = {
	promos: (params: PromotionPageParams): Promise<PromoPage> => request(`${BASE}/discounts?${toQuery(params)}`),
	promo: (id: string): Promise<Promo> => request(`${BASE}/discounts/${id}`),
	createPromo: (body: PromoCreate): Promise<Promo> => post(`${BASE}/discounts`, body),
	updatePromo: (id: string, body: PromoUpdate): Promise<Promo> => patch(`${BASE}/discounts/${id}`, body),
	removePromo: (id: string): Promise<void> => del(`${BASE}/discounts/${id}`),
	menus: (): Promise<PromoMenu[]> => request(`${BASE}/menus`),
	announcements: (params: PromotionPageParams): Promise<AnnouncementPage> => request(`${BASE}/announcements?${toQuery(params)}`),
	announcement: (id: string): Promise<Announcement> => request(`${BASE}/announcements/${id}`),
	createAnnouncement: (body: AnnouncementCreate): Promise<Announcement> => post(`${BASE}/announcements`, body),
	updateAnnouncement: (id: string, body: AnnouncementUpdate): Promise<Announcement> => patch(`${BASE}/announcements/${id}`, body),
	uploadImage: (id: string, file: Blob): Promise<Announcement> => upload(`${BASE}/announcements/${id}/image`, 'file', file),
	removeAnnouncement: (id: string): Promise<void> => del(`${BASE}/announcements/${id}`),
	promoBulk: bulkApi<PromoCreate, PromoUpdate>(`${BASE}/discounts`),
	announcementBulk: bulkApi<never, AnnouncementUpdate>(`${BASE}/announcements`)
};
