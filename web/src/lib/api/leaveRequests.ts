import { del, post, request, toQuery } from './http';
import type { LeaveDecision, LeaveRequest, LeaveRequestPage, LeaveStatus } from './types';

const BASE = '/web/management/leave-requests';

export type LeaveParams = { status?: LeaveStatus; search?: string; page?: number; size?: number };

export const leaveRequestsApi = {
	list: (params: LeaveParams): Promise<LeaveRequestPage> => request(`${BASE}?${toQuery(params)}`),
	decide: (id: string, body: LeaveDecision): Promise<LeaveRequest> => post(`${BASE}/${id}/decision`, body),
	remove: (id: string): Promise<void> => del(`${BASE}/${id}`)
};
