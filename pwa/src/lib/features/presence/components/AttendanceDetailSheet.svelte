<script lang="ts">
	import DetailList from '$lib/components/card/DetailList.svelte';
	import type { DetailListRow } from '$lib/components/card/types';
	import StatusBadge from '$lib/components/feedback/StatusBadge.svelte';
	import PhotoPair from '$lib/components/media/PhotoPair.svelte';
	import BottomSheet from '$lib/components/sheet/BottomSheet.svelte';
	import AppText from '$lib/components/text/AppText.svelte';
	import { clock, durationParts } from '$lib/format/datetime';
	import { formatRupiah, weekdayDateLabel } from '$lib/format/labels';
	import { t } from '$lib/text/t';
	import { LOCATION_MODE_OUTSIDE, type AttendanceDay } from '../presence.svelte';
	import AttendanceStatusBadge from './AttendanceStatusBadge.svelte';

	/** Detail satu hari kehadiran; baris yang tidak punya nilai tidak ditampilkan. */
	let { day, onDismiss }: { day: AttendanceDay; onDismiss: () => void } = $props();

	const none = t('attendance_detail_none');

	const distanceLabel = (distance: number | null, radius: number | null): string | null => {
		if (distance === null) return null;
		const meters = String(Math.round(distance));
		return radius !== null ? t('attendance_detail_distance_limit', meters, String(radius)) : t('attendance_detail_distance_value', meters);
	};
	const accuracyLabel = (accuracy: number | null): string | null => (accuracy === null ? null : t('attendance_detail_accuracy_value', String(Math.round(accuracy))));

	/** Baris keterangan lokasi: di luar lokasi memakai label peringatan, selain itu hanya bila ada catatan. */
	function locationRow(mode: string | null, note: string | null, outsideLabel: Parameters<typeof t>[0], noteLabel: Parameters<typeof t>[0]): [string, string] | null {
		const text = note?.trim() ? note : null;
		if (mode === LOCATION_MODE_OUTSIDE) return [t(outsideLabel), text ?? none];
		return text ? [t(noteLabel), text] : null;
	}

	const clockOut = $derived(clock(day.clockOut) ?? none);
	const work = $derived.by(() => {
		if (day.workMinutes === null) return null;
		const [hours, minutes] = durationParts(day.workMinutes);
		return t('format_duration', hours, minutes);
	});

	const plain = $derived.by((): DetailListRow[] => {
		const rows: DetailListRow[] = [];
		const add = (label: Parameters<typeof t>[0], value: string | null) => value && rows.push({ label: t(label), value });
		add('attendance_detail_work', work);
		if (day.lateMinutes > 0) add('attendance_detail_late', t('attendance_detail_late_value', String(day.lateMinutes)));
		if (day.penalty > 0) add('attendance_detail_penalty', formatRupiah(day.penalty));
		add('attendance_detail_distance_in', distanceLabel(day.distanceIn, day.radiusIn));
		add('attendance_detail_accuracy_in', accuracyLabel(day.accuracyIn));
		const inRow = locationRow(day.modeIn, day.locationNoteIn, 'attendance_detail_outside_in', 'attendance_detail_location_in');
		if (inRow) rows.push({ label: inRow[0], value: inRow[1] });
		add('attendance_detail_distance_out', distanceLabel(day.distanceOut, day.radiusOut));
		add('attendance_detail_accuracy_out', accuracyLabel(day.accuracyOut));
		const outRow = locationRow(day.modeOut, day.locationNoteOut, 'attendance_detail_outside_out', 'attendance_detail_location_out');
		if (outRow) rows.push({ label: outRow[0], value: outRow[1] });
		add('attendance_detail_reason', day.outsideScheduleReason?.trim() ? day.outsideScheduleReason : null);
		add('attendance_detail_note', day.note?.trim() ? day.note : null);
		return rows;
	});

	const rows = $derived<DetailListRow[]>([
		{ label: t('attendance_detail_date'), value: weekdayDateLabel(day.date) },
		{ label: t('attendance_detail_status'), valueContent: statusValue },
		...(day.shiftCode ? [{ label: t('attendance_detail_shift'), value: day.shiftCode }] : []),
		...(day.roleName ? [{ label: t('attendance_detail_role'), value: day.roleName }] : []),
		{ label: t('attendance_detail_clock_in'), value: clock(day.clockIn) ?? none },
		day.autoClosed ? { label: t('attendance_detail_clock_out'), valueContent: clockOutValue } : { label: t('attendance_detail_clock_out'), value: clockOut },
		...plain
	]);
</script>

{#snippet statusValue()}<AttendanceStatusBadge {day} />{/snippet}
{#snippet clockOutValue()}
	<span class="flex items-center gap-2">
		<AppText role="body">{clockOut}</AppText>
		<StatusBadge text={t('attendance_detail_auto_closed')} tone="warning" />
	</span>
{/snippet}

<BottomSheet title={t('attendance_detail_title')} {onDismiss}>
	<DetailList {rows} />
	<div class="pt-4">
		<PhotoPair first={{ url: day.photoInUrl, caption: t('attendance_detail_photo_in') }} second={{ url: day.photoOutUrl, caption: t('attendance_detail_photo_out') }} />
	</div>
</BottomSheet>
