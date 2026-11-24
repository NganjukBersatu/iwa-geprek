import { del, inBranch, patch, post, request, toQuery } from './http';
import type { StockAdjustment, StockCandidate, StockCard, StockCardPage, StockCardUpdate, StockCount, StockCountResult, StockItem, StockReceipt, StockSettings } from './types';

const BASE = '/web/management/stock-items';

export const stockItemsApi = {
	list: (onlyProblems: boolean, sort?: string): Promise<{ items: StockItem[]; total: number }> => request(`${BASE}?${toQuery({ only_problems: onlyProblems || undefined, sort })}`),
	detail: (id: string): Promise<StockItem> => request(`${BASE}/${id}`),
	candidates: (outletId: string): Promise<StockCandidate[]> => request(inBranch(`${BASE}/candidates`, outletId)),
	cards: (outletId: string, menuItemId: string, page: number, size: number, sort?: string): Promise<StockCardPage> => request(inBranch(`${BASE}/${menuItemId}/cards?${toQuery({ page, size, sort })}`, outletId)),
	receive: (outletId: string, body: StockReceipt): Promise<StockCard> => post(inBranch(`${BASE}/receipts`, outletId), body),
	adjust: (outletId: string, body: StockAdjustment): Promise<StockCard> => post(inBranch(`${BASE}/adjustments`, outletId), body),
	count: (outletId: string, body: StockCount): Promise<StockCountResult> => post(inBranch(`${BASE}/counts`, outletId), body),
	settings: (outletId: string, menuItemId: string, body: StockSettings): Promise<StockItem> => patch(inBranch(`${BASE}/${menuItemId}`, outletId), body),
	remove: (outletId: string, menuItemId: string): Promise<void> => del(inBranch(`${BASE}/${menuItemId}`, outletId)),
	updateCard: (cardId: string, body: StockCardUpdate): Promise<StockCard> => patch(`${BASE}/cards/${cardId}`, body),
	removeCard: (cardId: string): Promise<void> => del(`${BASE}/cards/${cardId}`)
};
