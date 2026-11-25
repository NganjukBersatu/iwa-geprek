import { parseDate } from '@internationalized/date';
import { DATE_PRESETS, formatRange, lastPickable, presetRange, type DateRange } from '$lib/date/range';
import { memoryKey, recall, remember, type MemoryValue } from '$lib/stores/memory';
import type { ActiveFilter, FilterDef, FilterOption, FilterValue, FilterValues } from './types';

function fromMemory(value: MemoryValue | null): FilterValue | null {
	return typeof value === 'number' ? null : value;
}

/** Every filter starts from what the account last picked under its id and writes every change back, on every page alike; a picked value that does not apply on this page is left out here and kept for the pages where it does. */
export class Filters {
	defs = $state<FilterDef[]>([]);
	values = $state<FilterValues>({});

	constructor(defs: FilterDef[]) {
		this.defs = defs;
		for (const def of defs) this.values[def.key] = fromMemory(recall(memoryKey.filter(def.key)));
	}

	/** Whether the list covers every branch: no branch is picked. */
	get allBranches(): boolean {
		return this.get('cabang') === null;
	}

	/** The filters that apply now; the others are not offered until their requirement is met. */
	get offered(): FilterDef[] {
		return this.defs.filter((def) => this.meets(def));
	}

	get active(): ActiveFilter[] {
		const result: ActiveFilter[] = [];
		for (const def of this.defs) {
			const text = this.text(def.key);
			if (text !== null) result.push({ key: def.key, label: def.label, text, loading: this.labelPending(def.key) });
		}
		return result;
	}

	get count(): number {
		return this.active.length;
	}

	/** The same options again change nothing, so a list that sets them on every load does not make its own query look new. */
	setOptions(key: string, options: FilterOption[]): void {
		const def = this.def(key);
		if (def?.kind !== 'select') return;
		const same = def.options.length === options.length && def.options.every((option, index) => option.value === options[index]!.value && option.label === options[index]!.label);
		if (!same) def.options = options;
	}

	set(key: string, value: FilterValue | null): void {
		this.values[key] = value;
		remember(memoryKey.filter(key), value);
	}

	clear(key: string): void {
		this.set(key, null);
	}

	clearAll(): void {
		for (const def of this.defs) this.clear(def.key);
	}

	/** The value in force: what was picked when it applies here, otherwise what an empty filter means on this page. */
	pick(key: string): FilterValue | null {
		const def = this.def(key);
		if (!def) return null;
		const picked = this.picked(def);
		if (picked !== null) return picked;
		if (def.empty === undefined) return null;
		return def.kind === 'date' ? { preset: def.empty } : def.empty;
	}

	get(key: string): string | null {
		const value = this.pick(key);
		return typeof value === 'string' ? value : null;
	}

	range(key: string): DateRange | null {
		const value = this.pick(key);
		if (!value || typeof value === 'string') return null;
		return 'preset' in value ? presetRange(value.preset) : value;
	}

	/** Whether this filter holds a value that applies here, picked by the account or brought by a link; an empty filter only has its page default. */
	chosen(key: string): boolean {
		return this.picked(this.def(key)) !== null;
	}

	/** Whether a picked option's label is still unknown: a remembered choice is in place before its options load, and its raw id is never shown. */
	labelPending(key: string): boolean {
		const def = this.def(key);
		const value = this.picked(def);
		return def?.kind === 'select' && typeof value === 'string' && !def.options.some((option) => option.value === value);
	}

	/** The text of a picked value; empty while its label is pending. An empty filter has none, whatever it means on this page. */
	text(key: string): string | null {
		const def = this.def(key);
		const value = this.picked(def);
		if (!def || value === null) return null;
		if (typeof value === 'string') {
			return def.kind === 'select' ? (def.options.find((option) => option.value === value)?.label ?? '') : value;
		}
		if ('preset' in value) {
			const presets = def.kind === 'date' ? (def.presets ?? DATE_PRESETS) : DATE_PRESETS;
			return presets.find((preset) => preset.value === value.preset)?.label ?? value.preset;
		}
		return formatRange(value);
	}

	private def(key: string): FilterDef | undefined {
		return this.defs.find((item) => item.key === key);
	}

	private meets(def: FilterDef): boolean {
		if (!def.requires) return true;
		const { key, value } = def.requires;
		return value === null ? this.pick(key) === null : this.get(key) === value;
	}

	/** The remembered value when it applies on this page; options not loaded yet count as applying until they arrive. */
	private picked(def: FilterDef | undefined): FilterValue | null {
		const value = def ? this.values[def.key] : null;
		if (!def || value === null || value === undefined || !this.meets(def)) return null;
		if (def.kind === 'select') {
			if (typeof value !== 'string') return null;
			return def.options.length === 0 || def.options.some((option) => option.value === value) ? value : null;
		}
		if (typeof value === 'string') return null;
		if ('preset' in value) return (def.presets ?? DATE_PRESETS).some((preset) => preset.value === value.preset) ? value : null;
		const last = lastPickable(def.reach);
		// Rentang yang melewati hari terakhir yang boleh dipangkas ke hari itu, sehingga tanggal dari tautan tetap terlihat di chip, tidak hilang ke rentang bawaan.
		if (last !== null && value.to > last) return { from: value.from > last ? last : value.from, to: last };
		// Rentang yang lebih panjang dari batas halaman dipangkas di ujungnya, dengan alasan yang sama seperti hari terakhir di atas.
		if (def.maxDays && parseDate(value.from).add({ days: def.maxDays }).compare(parseDate(value.to)) <= 0) {
			return { from: value.from, to: parseDate(value.from).add({ days: def.maxDays - 1 }).toString() };
		}
		return value;
	}
}
