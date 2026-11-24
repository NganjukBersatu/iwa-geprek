import { del, patch, request, toQuery } from './http';
import type { OrderNote, OrderNoteRename } from './types';

const BASE = '/web/management/order-notes';

export const orderNotesApi = {
	list: (sort?: string): Promise<OrderNote[]> => request(`${BASE}?${toQuery({ sort })}`),
	detail: (id: string): Promise<OrderNote> => request(`${BASE}/${id}`),
	rename: (note: OrderNote, body: OrderNoteRename): Promise<OrderNote> => patch(`${BASE}/${note.id}`, body),
	remove: (note: OrderNote): Promise<void> => del(`${BASE}/${note.id}`)
};
