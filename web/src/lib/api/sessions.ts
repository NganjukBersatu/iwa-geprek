import { del, patch, post, request, toQuery, type SortParam } from './http';
import type {
	OrderCatalog,
	OrderCorrection,
	SessionClosing,
	SessionCorrection,
	SessionHistoryPage,
	SessionHistoryRow,
	SessionImpact,
	SessionIntervention,
	SessionLines,
	SessionList,
	SessionOrder,
	SessionOrderDetail
} from './types';

const BASE = '/web/management/sessions';
const HISTORY = '/web/management/session-history';

export type SessionHistoryParams = SortParam & { start?: string; end?: string; running?: boolean; search?: string; page?: number; size?: number };

export const sessionsApi = {
	list: (params: SortParam & { start?: string; end?: string; limit: number }): Promise<SessionList> => request(`${BASE}?${toQuery(params)}`),
	lines: (sessionId: string): Promise<SessionLines> => request(`${BASE}/${sessionId}/lines`),
	history: (params: SessionHistoryParams): Promise<SessionHistoryPage> => request(`${HISTORY}?${toQuery(params)}`),
	historyDetail: (sessionId: string): Promise<SessionHistoryRow> => request(`${HISTORY}/${sessionId}`),
	correct: (sessionId: string, body: SessionCorrection): Promise<SessionHistoryRow> => patch(`${HISTORY}/${sessionId}`, body),
	impact: (sessionId: string): Promise<SessionImpact> => request(`${HISTORY}/${sessionId}/impact`),
	closing: (sessionId: string): Promise<SessionClosing> => request(`${HISTORY}/${sessionId}/closing`),
	close: (sessionId: string, body: SessionIntervention): Promise<SessionHistoryRow> => post(`${HISTORY}/${sessionId}/close`, body),
	remove: (sessionId: string): Promise<void> => del(`${HISTORY}/${sessionId}`),
	orders: (sessionId: string, sort?: string): Promise<SessionOrder[]> => request(`${HISTORY}/${sessionId}/orders?${toQuery({ sort })}`),
	openBills: (sessionId: string): Promise<SessionOrder[]> => request(`${HISTORY}/${sessionId}/open-bills`),
	order: (orderId: string): Promise<SessionOrderDetail> => request(`${HISTORY}/orders/${orderId}`),
	catalog: (orderId: string): Promise<OrderCatalog> => request(`${HISTORY}/orders/${orderId}/catalog`),
	correctOrder: (orderId: string, body: OrderCorrection): Promise<SessionOrder> => patch(`${HISTORY}/orders/${orderId}`, body),
	removeOrder: (orderId: string): Promise<void> => del(`${HISTORY}/orders/${orderId}`),
	voidOrder: (orderId: string, reason: string): Promise<SessionOrder> => post(`${HISTORY}/orders/${orderId}/void`, { reason })
};
