import { request } from './http';
import type { ScreenAccess } from './types';

export const screensApi = {
	mine: (): Promise<ScreenAccess> => request('/web/management/screens')
};
