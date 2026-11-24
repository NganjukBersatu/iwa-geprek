import { termText } from '$lib/text/terms';
import { promotionText } from '$lib/text/promotions';
export const KIND_LABELS: Record<string, string> = { basic: promotionText.wholeOrder, produk: promotionText.specificMenus, total: promotionText.minimumPurchase };
export const STATUS_LABELS: Record<string, string> = { berlaku: promotionText.active, terjadwal: promotionText.scheduled, berakhir: promotionText.ended, nonaktif: termText.inactive };
export const STATUS_TONES = { berlaku: 'success', terjadwal: 'info', berakhir: 'neutral', nonaktif: 'neutral' } as const;
