import type { BulkResult } from '$lib/api/types';
import { controlText } from '$lib/text/controls';
import { format } from '$lib/text/format';

export function summarize(result: BulkResult, verb: string): string {
	if (result.failed === 0) return format(controlText.bulkSucceeded, { count: result.succeeded, verb: verb });
	if (result.succeeded === 0) return format(controlText.bulkAllFailed, { count: result.failed });
	return format(controlText.bulkPartial, { succeeded: result.succeeded, verb: verb, failed: result.failed });
}
