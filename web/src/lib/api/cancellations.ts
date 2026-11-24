import { post, request, toQuery } from './http';
import type { CancellationDecision, CancellationPage } from './types';

const BASE = '/web/management/cancellations';

export type CancellationParams = { page?: number; size?: number };

export const cancellationsApi = {
	list: (params: CancellationParams): Promise<CancellationPage> => request(`${BASE}?${toQuery(params)}`),
	decide: (id: string, body: CancellationDecision): Promise<void> => post(`${BASE}/${id}/decision`, body)
};
