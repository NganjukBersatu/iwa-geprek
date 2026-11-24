import { patch, request, toQuery } from './http';
import type { ReleaseRead } from './types';

const BASE = '/web/management';

export const releasesApi = {
	read: (version: string): Promise<ReleaseRead> => request(`${BASE}/release-read?${toQuery({ version })}`),
	markRead: (version: string): Promise<ReleaseRead> => patch(`${BASE}/release-read`, { version })
};
