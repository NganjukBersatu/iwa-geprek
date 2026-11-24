import { bulkApi } from './bulk';
import { del, inBranch, post, put, request, toQuery } from './http';
import type {
	IngredientClosingPeriod,
	IngredientOpeningStatus,
	IngredientCount,
	IngredientCountChanges,
	IngredientCountClose,
	IngredientCountDraft,
	IngredientCountDraftLines,
	IngredientCountDetail,
	IngredientCountLines,
	IngredientCountOpenSessions,
	IngredientCountRunning,
	IngredientOpening,
	StockReport
} from './types';

const BASE = '/web/management/ingredient-counts';

export const ingredientCountsApi = {
	list: (sort?: string, source?: string): Promise<IngredientCount[]> => request(`${BASE}?${toQuery({ sort, source })}`),
	running: (): Promise<IngredientCountRunning[]> => request(`${BASE}/running`),
	detail: (id: string, partStart: string | null = null): Promise<IngredientCountDetail> => request(partStart ? `${BASE}/${id}?part_start=${encodeURIComponent(partStart)}` : `${BASE}/${id}`),
	changes: (id: string, sort: string | undefined, page: number, size: number): Promise<IngredientCountChanges> => request(`${BASE}/${id}/changes?${toQuery({ sort, page, size })}`),
	draft: (outletId: string): Promise<IngredientCountDraft> => request(inBranch(`${BASE}/draft`, outletId)),
	saveDraft: (outletId: string, body: IngredientCountDraftLines): Promise<void> => put(inBranch(`${BASE}/draft`, outletId), body),
	sheet: (outletId: string, range: { start: string; end: string; sort?: string }): Promise<StockReport> => request(inBranch(`${BASE}/sheet?${toQuery(range)}`, outletId)),
	openingStatus: (outletId: string, start: string): Promise<IngredientOpeningStatus> => request(inBranch(`${BASE}/opening-status?start=${encodeURIComponent(start)}`, outletId)),
	closingPeriod: (outletId: string): Promise<IngredientClosingPeriod> => request(inBranch(`${BASE}/closing-period`, outletId)),
	openSessions: (outletId: string, end: string): Promise<IngredientCountOpenSessions> => request(inBranch(`${BASE}/open-sessions?${toQuery({ end })}`, outletId)),
	close: (outletId: string, body: IngredientCountClose): Promise<IngredientCountDetail> => post(inBranch(BASE, outletId), body),
	setLines: (id: string, body: IngredientCountLines): Promise<IngredientCountDetail> => put(`${BASE}/${id}/lines`, body),
	cancel: (id: string): Promise<void> => del(`${BASE}/${id}`),
	opening: bulkApi<IngredientOpening, never>(`${BASE}/opening`)
};
