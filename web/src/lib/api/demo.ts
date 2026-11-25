import { request } from './http';
import type { DemoStatus, LoginResponse } from './types';

const BASE = '/v2/demo';

export const demoApi = {
	status: (): Promise<DemoStatus> => request(BASE, undefined, false),
	start: (): Promise<DemoStatus> => request(BASE, { method: 'POST' }, false),
	// Server memasang cookie sesi untuk akun pemilik demo, sama seperti masuk biasa.
	enter: (): Promise<LoginResponse> => request(`${BASE}/session`, { method: 'POST' }, false),
	leave: (): Promise<void> => request(BASE, { method: 'DELETE' }, false)
};
