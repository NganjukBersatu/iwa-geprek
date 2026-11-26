import { post, request, toQuery } from './http';
import type { Cancellation, CancellationDecision, CancellationPage } from './types';

const BASE = '/web/management/cancellations';

export type CancellationParams = { page?: number; size?: number };

export const cancellationsApi = {
	list: (params: CancellationParams): Promise<CancellationPage> => request(`${BASE}?${toQuery(params)}`),
	detail: (id: string): Promise<Cancellation> => request(`${BASE}/${id}`),
	decide: (id: string, body: CancellationDecision): Promise<void> => post(`${BASE}/${id}/decision`, body)
};
