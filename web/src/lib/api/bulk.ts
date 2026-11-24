import { inBranch, post } from './http';
import type { BulkResult } from './types';

export function bulkApi<Create, Changes>(base: string) {
	return {
		create: (items: Create[]): Promise<BulkResult> => post(`${base}/bulk`, { items }),
		/** Rows that belong to one branch go to the branch chosen for them, whatever the filter shows. */
		createIn: (outletId: string, items: Create[]): Promise<BulkResult> => post(inBranch(`${base}/bulk`, outletId), { items }),
		update: (ids: string[], changes: Changes): Promise<BulkResult> => post(`${base}/bulk-update`, { ids, changes }),
		remove: (ids: string[]): Promise<BulkResult> => post(`${base}/bulk-delete`, { ids })
	};
}
