import { postForFile } from './http';
import type { ExportRequest } from './types';

export const exportsApi = {
	table: (body: ExportRequest): Promise<{ blob: Blob; filename: string | null }> => postForFile('/web/management/exports/table', body)
};
