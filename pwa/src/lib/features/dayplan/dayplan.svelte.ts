import type { DayPlanDto, SegmentDto } from '$lib/api/types';
import { current } from '$lib/auth/current.svelte';
import { epochOf, stampAt, type WibStamp } from '$lib/format/datetime';

export type SegmentKind = 'work' | 'scheduled-overtime' | 'unplanned-overtime';

/** Satu rentang waktu hari ini milik karyawan, dengan jam nyata dalam detik epoch dan dalam WIB. */
export type DaySegment = {
	kind: SegmentKind;
	startEpoch: number;
	endEpoch: number;
	start: WibStamp;
	end: WibStamp;
	minutes: number;
	code: string | null;
	colorHex: string | null;
	isOvertime: boolean;
};

const KINDS: Record<string, SegmentKind> = { work: 'work', scheduled_overtime: 'scheduled-overtime', unplanned_overtime: 'unplanned-overtime' };

function segmentOf(dto: SegmentDto): DaySegment | null {
	const kind = KINDS[dto.kind];
	const startEpoch = epochOf(dto.starts_at);
	const endEpoch = epochOf(dto.ends_at);
	if (!kind || startEpoch === null || endEpoch === null) return null;
	return { kind, startEpoch, endEpoch, start: stampAt(startEpoch), end: stampAt(endEpoch), minutes: dto.minutes, code: dto.code, colorHex: dto.color, isOvertime: kind !== 'work' };
}

/** Rentang yang sedang berlaku: lembur menyala saat jamnya tiba, jam kerja menyala selama sudah absen datang, belum absen pulang, dan belum lewat jam selesai. */
export function activeSegment(segments: readonly DaySegment[], nowEpoch: number, clockedIn: boolean): DaySegment | null {
	return (
		segments.find((segment) => segment.isOvertime && nowEpoch >= segment.startEpoch && nowEpoch < segment.endEpoch) ??
		segments.find((segment) => !segment.isOvertime && clockedIn && nowEpoch < segment.endEpoch) ??
		null
	);
}

export class DayPlanState {
	segments = $state<DaySegment[]>([]);
	/** Lembur terjadwal hari ini, bila ada; menghalangi pencatatan lembur dadakan. */
	scheduledOvertime = $state<DaySegment | null>(null);

	async load(onSessionExpired: () => void): Promise<void> {
		const result = await current.api().read<DayPlanDto>('/v2/day-plan');
		if (result.kind === 'unauthorized') return onSessionExpired();
		if (result.kind !== 'success') return;
		this.segments = result.value.segments.map(segmentOf).filter((segment): segment is DaySegment => segment !== null).sort((a, b) => a.startEpoch - b.startEpoch);
		this.scheduledOvertime = result.value.scheduled_overtime ? segmentOf(result.value.scheduled_overtime) : null;
	}
}
