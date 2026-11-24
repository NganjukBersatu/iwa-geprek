import { current } from '$lib/auth/current.svelte';
import type { AppFailure } from '$lib/failure/failure';
import { t } from '$lib/text/t';

export const PERFORMANCE_RANGES = [
	{ key: 'cycle', label: 'performance_range_cycle' },
	{ key: 'previous', label: 'performance_range_previous' },
	{ key: 'all', label: 'performance_range_all' }
] as const;
export type PerformanceRange = (typeof PERFORMANCE_RANGES)[number];

export type Performance = {
	start: string;
	end: string;
	countedDays: number;
	buckets: { start: string; onTimePercent: number | null; workMinutes: number; overtimeMinutes: number; tasksDone: number }[];
	composition: { onTime: number; late: number; leave: number; absent: number };
	workMinutes: number;
	overtimeMinutes: number;
	tasksAssigned: number;
	tasksDone: number;
	/** Bintang 0 sampai 5 kelipatan 0,5; null bila belum cukup data. */
	rating: { stars: number | null; groups: { key: string; components: { key: string; percent: number | null }[] }[] };
};

type PerformanceResponse = {
	start: string;
	end: string;
	counted_days?: number;
	buckets?: { start: string; on_time_percent?: number | null; work_minutes?: number; overtime_minutes?: number; tasks_done?: number }[];
	composition?: { on_time?: number; late?: number; leave?: number; absent?: number };
	tasks_assigned?: number;
	tasks_done?: number;
	rating?: { stars?: number | null; groups?: { key: string; components?: { key: string; percent?: number | null }[] }[] };
};

function performanceOf(dto: PerformanceResponse): Performance {
	const buckets = (dto.buckets ?? []).map((bucket) => ({
		start: bucket.start,
		onTimePercent: bucket.on_time_percent ?? null,
		workMinutes: bucket.work_minutes ?? 0,
		overtimeMinutes: bucket.overtime_minutes ?? 0,
		tasksDone: bucket.tasks_done ?? 0
	}));
	return {
		start: dto.start,
		end: dto.end,
		countedDays: dto.counted_days ?? 0,
		buckets,
		composition: { onTime: dto.composition?.on_time ?? 0, late: dto.composition?.late ?? 0, leave: dto.composition?.leave ?? 0, absent: dto.composition?.absent ?? 0 },
		workMinutes: buckets.reduce((sum, bucket) => sum + bucket.workMinutes, 0),
		overtimeMinutes: buckets.reduce((sum, bucket) => sum + bucket.overtimeMinutes, 0),
		tasksAssigned: dto.tasks_assigned ?? 0,
		tasksDone: dto.tasks_done ?? 0,
		rating: {
			stars: dto.rating?.stars ?? null,
			groups: (dto.rating?.groups ?? []).map((group) => ({ key: group.key, components: (group.components ?? []).map((component) => ({ key: component.key, percent: component.percent ?? null })) }))
		}
	};
}

const GROUP_LABELS: Record<string, Parameters<typeof t>[0]> = { behavior: 'performance_rating_group_behavior', work: 'performance_rating_group_work' };
const COMPONENT_LABELS: Record<string, Parameters<typeof t>[0]> = {
	on_time: 'performance_slice_on_time',
	attendance: 'performance_rating_attendance',
	given_tasks_done: 'performance_rating_given_tasks_done',
	given_tasks_in_time: 'performance_rating_given_tasks_in_time',
	own_tasks_done: 'performance_rating_own_tasks_done',
	own_tasks_in_time: 'performance_rating_own_tasks_in_time'
};

export const groupLabel = (key: string): string => (GROUP_LABELS[key] ? t(GROUP_LABELS[key]) : key);
export const componentLabel = (key: string): string => (COMPONENT_LABELS[key] ? t(COMPONENT_LABELS[key]) : key);
export const percentText = (percent: number | null): string => (percent === null ? '—' : `${Math.round(percent)}%`);

/** Bintang dengan satu angka di belakang koma memakai koma, misalnya 4,5. */
export function starsText(stars: number): string {
	const tenths = Math.round(stars * 10);
	return `${Math.floor(tenths / 10)},${tenths % 10}`;
}

/** Keadaan halaman Kinerja: pilihan rentang dan hasil perhitungan server. */
export class PerformanceState {
	range = $state.raw<PerformanceRange>(PERFORMANCE_RANGES[0]);
	performance = $state<Performance | null>(null);
	loading = $state(true);
	failure = $state<AppFailure | null>(null);

	private token = 0;

	constructor(private readonly onSessionExpired: () => void) {}

	select(range: PerformanceRange): void {
		if (range !== this.range) void this.load(range);
	}

	retry(): void {
		void this.load(this.range);
	}

	async load(range: PerformanceRange = this.range): Promise<void> {
		const token = ++this.token;
		this.range = range;
		this.loading = true;
		this.failure = null;
		const result = await current.api().read<PerformanceResponse>('/v2/performance', { range: range.key });
		if (token !== this.token) return;
		if (result.kind === 'unauthorized') return this.onSessionExpired();
		this.loading = false;
		if (result.kind === 'success') this.performance = performanceOf(result.value);
		else this.failure = result.failure;
	}
}
