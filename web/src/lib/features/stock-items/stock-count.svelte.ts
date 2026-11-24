import { controlText } from '$lib/text/controls';
import { api } from '$lib/api';
import type { StockItem } from '$lib/api/types';
import { userMessage } from '$lib/api/user-message';
import { toast } from '$lib/components/feedback/toast.svelte';
import { parseNumber } from '$lib/format/number';
import { stockItemText } from '$lib/text/stock-items';
import { format } from '$lib/text/format';

/** A count sheet of the resold items of one branch: what is typed is the physical figure, and only the difference is written. */
export class StockCountState {
	branch = $state('');
	items = $state<StockItem[]>([]);
	counted = $state<Record<string, string>>({});
	note = $state('');
	problem = $state('');
	error = $state('');
	loading = $state(false);
	busy = $state(false);

	get filled(): number {
		return Object.values(this.counted).filter((text) => text.trim() !== '').length;
	}

	/** Another branch starts the sheet over, since a count belongs to one branch. */
	async changeBranch(): Promise<void> {
		this.counted = {};
		this.items = [];
		this.problem = '';
		this.error = '';
		if (!this.branch) return;
		this.loading = true;
		try {
			const page = await api.stockItems.list(false);
			this.items = page.items.filter((item) => item.outlet_id === this.branch);
		} catch (error) {
			this.error = userMessage(error, stockItemText.itemsLoadFailed);
		} finally {
			this.loading = false;
		}
	}

	/** True when the count was saved, so the page returns to the list. */
	async submit(): Promise<boolean> {
		const lines: { menu_item_id: string; counted: string }[] = [];
		for (const [menuItemId, text] of Object.entries(this.counted)) {
			if (!text.trim()) continue;
			const value = parseNumber(text);
			if (value === null || value < 0) {
				this.problem = controlText.countedInvalid;
				return false;
			}
			lines.push({ menu_item_id: menuItemId, counted: String(value) });
		}
		if (!this.branch) {
			this.problem = stockItemText.countBranchRequired;
			return false;
		}
		if (lines.length === 0) {
			this.problem = stockItemText.countedRequired;
			return false;
		}
		this.problem = '';
		this.error = '';
		this.busy = true;
		try {
			const result = await api.stockItems.count(this.branch, { lines, note: this.note.trim() || null });
			toast.show(result.adjusted === 0 ? stockItemText.countAllMatch : format(stockItemText.itemsAdjusted, { count: result.adjusted }));
			return true;
		} catch (error) {
			this.error = userMessage(error, stockItemText.countSaveFailed);
			return false;
		} finally {
			this.busy = false;
		}
	}
}
