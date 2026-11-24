import { del, post, put, request, toQuery, upload } from './http';
import type { Sop, SopDraftDetail, SopDraftInput, SopDraftSummary, SopInput, SopMedia, SopReaderPage, SopSummary } from './types';

export type SopReaderQuery = { outlet_id?: string; read?: boolean; sort?: string; page: number; size: number };

const BASE = '/web/management/sop';

export const sopApi = {
	list: (sort?: string): Promise<SopSummary[]> => request(`${BASE}?${toQuery({ sort })}`),
	get: (id: string): Promise<Sop> => request(`${BASE}/${id}`),
	readers: (id: string, query: SopReaderQuery): Promise<SopReaderPage> => request(`${BASE}/${id}/readers?${toQuery(query)}`),
	create: (body: SopInput): Promise<Sop> => post(BASE, body),
	update: (id: string, body: SopInput): Promise<Sop> => put(`${BASE}/${id}`, body),
	remove: (id: string): Promise<void> => del(`${BASE}/${id}`),
	reorder: (ids: string[]): Promise<SopSummary[]> => put(`${BASE}/order`, { ids }),
	uploadMedia: (file: Blob): Promise<SopMedia> => upload(`${BASE}/media`, 'file', file),
	drafts: (): Promise<SopDraftSummary[]> => request(`${BASE}/drafts`),
	draft: (id: string): Promise<SopDraftDetail> => request(`${BASE}/drafts/${id}`),
	saveDraft: (body: SopDraftInput): Promise<SopDraftSummary> => put(`${BASE}/drafts`, body),
	discardDraft: (id: string): Promise<void> => del(`${BASE}/drafts/${id}`)
};
