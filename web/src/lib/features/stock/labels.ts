import { termText } from '$lib/text/terms';
import type { ReplacementStatus } from '$lib/api/types';
import { EMPTY_VALUE } from '$lib/format/currency';
import { stockReportText } from '$lib/text/stock-report';

export const REPLACEMENT: Record<ReplacementStatus, { label: string; tone: 'danger' | 'warning' | 'muted' }> = {
	replace: { label: termText.yes, tone: 'danger' },
	check: { label: stockReportText.review, tone: 'warning' },
	tolerated: { label: stockReportText.no, tone: 'muted' },
	uncounted: { label: EMPTY_VALUE, tone: 'muted' }
};
