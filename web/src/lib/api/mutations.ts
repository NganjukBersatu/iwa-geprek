import { request, toQuery, type SortParam } from './http';
import type { MutationDetail, MutationPage } from './types';

const BASE = '/web/management/mutations';

export const mutationsApi = {
	list: (params: SortParam & { start?: string; end?: string; page?: number; size?: number }): Promise<MutationPage> => request(`${BASE}?${toQuery(params)}`),
	detail: (sessionId: string): Promise<MutationDetail> => request(`${BASE}/${sessionId}`)
};
