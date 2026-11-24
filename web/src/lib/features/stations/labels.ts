import { controlText } from '$lib/text/controls';
import type { StationKind, StationStage, StationTiming } from '$lib/api/types';
import { EMPTY_VALUE, formatNumber } from '$lib/format/currency';
import { stationText } from '$lib/text/stations';
import { format } from '$lib/text/format';

const SECONDS_PER_MINUTE = 60;
const SECONDS_PER_HOUR = 3600;
const PERCENT = 100;

export const KIND_LABEL: Record<StationKind, string> = { make: stationText.roleMaker, deliver: stationText.roleRunner, handover: stationText.roleHandover };

export const KIND_HINT: Record<StationKind, string> = {
	make: stationText.roleMakerHint,
	deliver: stationText.roleRunnerHint,
	handover: stationText.roleHandoverHint
};

export const STAGE_LABEL: Record<StationStage, string> = { waiting: stationText.waiting, started: stationText.processing, finished: stationText.finished };

export const STEP_LABEL: Record<string, string> = {
	arrive: stationText.entered,
	start: stationText.started,
	finish: stationText.finished,
	undo: stationText.returned,
	acknowledge: stationText.acknowledged
};

export function formatSeconds(value: number | string | null | undefined): string {
	if (value === null || value === undefined) return EMPTY_VALUE;
	const total = Math.max(0, Math.round(Number(value)));
	const hours = Math.floor(total / SECONDS_PER_HOUR);
	const minutes = Math.floor((total % SECONDS_PER_HOUR) / SECONDS_PER_MINUTE);
	const seconds = total % SECONDS_PER_MINUTE;
	if (hours > 0) return format(stationText.dayAtTime, { day: hours, time: minutes });
	if (minutes > 0) return seconds > 0 ? format(stationText.minutesSeconds, { minutes: minutes, seconds: seconds }) : format(controlText.minutesCount, { count: minutes });
	return format(stationText.secondsCount, { count: seconds });
}

export function formatRatio(value: string | null): string {
	return value === null ? EMPTY_VALUE : `${formatNumber(Number(value) * PERCENT, 1)}%`;
}

export function formatTarget(seconds: number | null): string {
	return seconds === null ? stationText.recordOnly : formatSeconds(seconds);
}

export const timingCaption = (timing: StationTiming): string => format(stationText.itemsCount, { count: formatNumber(timing.tasks, 0) });
