import { termText } from '$lib/text/terms';
import { stockItemText } from '$lib/text/stock-items';
export const STOCK_STATUS: Record<string, { label: string; tone: 'danger' | 'warning' | 'success' }> = {
	habis: { label: termText.outOfStock, tone: 'danger' },
	menipis: { label: stockItemText.low, tone: 'warning' },
	aman: { label: stockItemText.safe, tone: 'success' }
};

export const CARD_KINDS: Record<string, string> = { masuk: stockItemText.kindReceived, keluar: stockItemText.kindSold, penyesuaian: stockItemText.kindAdjusted };
