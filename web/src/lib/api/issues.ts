import { request } from './http';
import type { IssueReport } from './types';

export const issuesApi = {
	list: (): Promise<IssueReport> => request('/web/management/issues')
};
