import { termText } from '$lib/text/terms';
import { turnoverText } from '$lib/text/turnover';
export const statusLabels = { out: termText.outOfStock, urgent: turnoverText.buyNow, dormant: turnoverText.idle, slow: turnoverText.slow, safe: turnoverText.safe } as const;
