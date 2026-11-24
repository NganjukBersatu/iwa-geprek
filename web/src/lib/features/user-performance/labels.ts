import type { PerformanceRange } from '$lib/api/userPerformance';
import { formatDate } from '$lib/date/range';
import { EMPTY_VALUE, formatNumber } from '$lib/format/currency';
import { format } from '$lib/text/format';
import { userPerformanceText as t } from '$lib/text/user-performance';

export const RANGE_LABELS: Record<PerformanceRange, string> = t.ranges;

const GROUP_LABELS: Record<string, string> = t.groups;
const COMPONENT_LABELS: Record<string, string> = t.components;

export const groupLabel = (key: string): string => GROUP_LABELS[key] ?? key;
export const componentLabel = (key: string): string => COMPONENT_LABELS[key] ?? key;

/** Stars with one digit after the comma, for example 4,5 of 5. */
export const starsText = (stars: number | null): string => (stars === null ? t.noRating : format(t.starsOutOf, { stars: formatNumber(stars, 1) }));

export const percentText = (percent: number | null): string => (percent === null ? EMPTY_VALUE : `${Math.round(percent)}%`);

export const periodText = (start: string, end: string): string => `${formatDate(start)} – ${formatDate(end)}`;
