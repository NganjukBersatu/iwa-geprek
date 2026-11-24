import type { DatePreset, DateRange, DateReach } from '$lib/date/range';

export type FilterOption = { value: string; label: string };

/** A filter that only applies while another one holds a value; null means while the other is empty. */
export type FilterRequirement = { key: string; value: string | null };

type FilterDefBase = {
	key: string;
	label: string;
	requires?: FilterRequirement;
};

export type SelectFilterDef = FilterDefBase & {
	kind: 'select';
	options: FilterOption[];
	/** What the list shows while nothing is picked; never shown as a chip or remembered. */
	empty?: string;
};

export type DateFilterDef = FilterDefBase & {
	kind: 'date';
	presets?: DatePreset[];
	reach: DateReach;
	maxDays?: number;
	/** The preset the list shows while no range is picked; never shown as a chip or remembered. */
	empty?: string;
};

export type FilterDef = SelectFilterDef | DateFilterDef;

export type DateFilterValue = { preset: string } | DateRange;

export type FilterValue = string | DateFilterValue;

export type FilterValues = Record<string, FilterValue | null>;

/** `loading` marks a picked option whose label has not arrived yet; the chip shows a placeholder in its place. */
export type ActiveFilter = { key: string; label: string; text: string; loading: boolean };
