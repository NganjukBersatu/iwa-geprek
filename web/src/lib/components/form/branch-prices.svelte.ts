import { SvelteSet } from 'svelte/reactivity';
import { rupiahDigits, rupiahInput } from '$lib/format/currency';
import { termText } from '$lib/text/terms';

export const ALL_BRANCHES_TEXT = termText.allBranches;

/** Anything sold per branch: outlet_ids null means every branch, branch_prices holds only the branches with a price of their own. */
export type BranchPriced = { outlet_ids: string[] | null; branch_prices: Record<string, string> };
export type BranchOption = { id: string; name: string };

export function sellsAt(item: BranchPriced, outletId: string): boolean {
	return item.outlet_ids === null || item.outlet_ids.includes(outletId);
}

export function sellingOutlets(item: BranchPriced, outlets: BranchOption[]): BranchOption[] {
	return outlets.filter((outlet) => sellsAt(item, outlet.id));
}

/** The same "sold at" text for every list and detail; a branch not loaded yet is written as its id. */
export function sellersText(item: BranchPriced, outlets: BranchOption[]): string {
	if (item.outlet_ids === null) return ALL_BRANCHES_TEXT;
	return item.outlet_ids.map((id) => outlets.find((outlet) => outlet.id === id)?.name ?? id).join(', ');
}

/** The price in force at one branch: that branch's own price when it has one, otherwise the base price. */
export function branchPriceOf(item: BranchPriced & { price: string }, outletId: string): { price: string; own: boolean } {
	const own = item.branch_prices[outletId];
	return own === undefined ? { price: item.price, own: false } : { price: own, own: true };
}

export function branchPriceCount(item: BranchPriced): number {
	return Object.keys(item.branch_prices).length;
}

/** The selling branches and their prices, one rule for menus, extras, and anything else sold per branch. */
export class BranchPriceForm {
	everywhere = $state(true);
	readonly sellers: SvelteSet<string>;
	private prices = $state<Record<string, string>>({});
	private readonly initial: Record<string, string>;

	constructor(current: BranchPriced | null) {
		this.initial = Object.fromEntries(Object.entries(current?.branch_prices ?? {}).map(([id, price]) => [id, rupiahInput(price)]));
		this.prices = { ...this.initial };
		this.everywhere = current ? current.outlet_ids === null : true;
		this.sellers = new SvelteSet(current?.outlet_ids ?? []);
	}

	get noSeller(): boolean {
		return !this.everywhere && this.sellers.size === 0;
	}

	priceOf(outletId: string): string {
		return this.prices[outletId] ?? '';
	}

	setPrice(outletId: string, value: string): void {
		this.prices[outletId] = value;
	}

	sells(outletId: string): boolean {
		return this.sellers.has(outletId);
	}

	toggleEverywhere(): void {
		this.everywhere = !this.everywhere;
	}

	toggleSeller(outletId: string): void {
		if (this.sellers.has(outletId)) this.sellers.delete(outletId);
		else this.sellers.add(outletId);
	}

	outletIds(): string[] | null {
		return this.everywhere ? null : [...this.sellers];
	}

	/** A branch price emptied is sent as null so the server removes it. */
	branchPrices(outlets: BranchOption[]): Record<string, string | null> {
		const result: Record<string, string | null> = {};
		for (const outlet of outlets) {
			const typed = rupiahDigits(this.priceOf(outlet.id));
			if (typed) result[outlet.id] = typed;
			else if (outlet.id in this.initial) result[outlet.id] = null;
		}
		return result;
	}
}

/** Item milik satu cabang (outlet_id) atau semua cabang bila kosong. */
export function scopeText(outletId: string | null, outlets: BranchOption[]): string {
	if (outletId === null) return ALL_BRANCHES_TEXT;
	return outlets.find((outlet) => outlet.id === outletId)?.name ?? outletId;
}
