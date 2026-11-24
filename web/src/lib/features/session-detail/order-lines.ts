import type { OrderCatalogMenu, SessionOrderItem } from '$lib/api/types';

/** One line of an order being corrected; `key` only tells rows apart in the dialog, the server gives every saved line its own id. */
export type EditableLine = {
	key: string;
	menu_item_id: string;
	qty: number;
	note: string;
	variant_ids: string[];
	extras: { extra_id: string; qty: number }[];
};

export const newKey = (): string => crypto.randomUUID();

export function fromItem(item: SessionOrderItem): EditableLine {
	return {
		key: newKey(),
		menu_item_id: item.menu_item_id ?? '',
		qty: item.qty,
		note: item.note ?? '',
		variant_ids: [...item.variant_ids],
		extras: item.extras.filter((extra) => extra.extra_id).map((extra) => ({ extra_id: extra.extra_id as string, qty: extra.qty }))
	};
}

export function blankLine(menu: OrderCatalogMenu | undefined): EditableLine {
	return { key: newKey(), menu_item_id: menu?.id ?? '', qty: 1, note: '', variant_ids: [], extras: [] };
}

/** The shape the server takes, without the dialog's own key. */
export function toBody(line: EditableLine) {
	return { menu_item_id: line.menu_item_id, qty: line.qty, note: line.note.trim() || null, variant_ids: line.variant_ids, extras: line.extras };
}

/** What a line costs on screen: a menu already on the order keeps the price it was sold at, the rest uses today's price. */
export function lineTotal(line: EditableLine, menu: OrderCatalogMenu | undefined, soldAt: Map<string, number>): number {
	if (!menu) return 0;
	const price = soldAt.get(menu.id) ?? Number(menu.price);
	const extras = line.extras.reduce((sum, pick) => sum + Number(menu.extras.find((extra) => extra.id === pick.extra_id)?.price ?? 0) * pick.qty, 0);
	return (price + extras) * line.qty;
}
