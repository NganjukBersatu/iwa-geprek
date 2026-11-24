<script lang="ts">
	import { untrack } from 'svelte';
	import { api } from '$lib/api';
	import type { AttendanceEdit, AttendanceRecord } from '$lib/api/types';
	import Button from '$lib/components/button/Button.svelte';
	import Badge from '$lib/components/card/Badge.svelte';
	import Card from '$lib/components/card/Card.svelte';
	import FigureList from '$lib/components/card/FigureList.svelte';
	import { formatDate } from '$lib/date/range';
	import { EMPTY_VALUE, formatRupiah } from '$lib/format/currency';
	import { formatDateTime, formatDuration, formatTime } from '$lib/format/datetime';
	import { PAGES } from '$lib/nav/pages';
	import { recordText } from '$lib/text/record-detail';
	import RecordDetailView from '../../record-detail/components/RecordDetailView.svelte';
	import { RecordDetailState } from '../../record-detail/record-detail.svelte';
	import type { MapView } from '../attendance-list.svelte';
	import { STATUS_LABELS, STATUS_TONES } from '../labels';
	import AttendanceEditForm from './AttendanceEditForm.svelte';
	import LocationDialog from './LocationDialog.svelte';
	import { attendanceListText } from '$lib/text/attendance-list';
	import { termText } from '$lib/text/terms';
	import { scheduleText } from '$lib/text/schedule';
	import { format } from '$lib/text/format';
	import RichText from '$lib/components/text/RichText.svelte';

	let { id }: { id: string } = $props();

	const detail = new RecordDetailState<AttendanceRecord, AttendanceEdit>(untrack(() => id), {
		load: (recordId) => api.attendance.detail(recordId),
		update: (record, body) => api.attendance.edit(record.id, body),
		remove: (record) => api.attendance.remove(record.id),
		name: (record) => record.name || record.username,
		text: recordText('catatan kehadiran', PAGES.attendance.label)
	});

	let map = $state<MapView | null>(null);

	const proofs = (record: AttendanceRecord) => [
		{ side: 'in' as const, caption: attendanceListText.checkIn, at: record.clock_in_at, proof: record.clock_in },
		{ side: 'out' as const, caption: attendanceListText.checkOut, at: record.clock_out_at, proof: record.clock_out }
	];
</script>

<RecordDetailView
	{detail}
	back={PAGES.attendance}
	trail={(record) => [{ label: PAGES.attendance.label, href: PAGES.attendance.path }, { label: `${record.name || record.username} · ${formatDate(record.date)}` }]}
	tables={['attendance_records', 'schedules']}
	title={(record) => record.name || record.username}
	description={(record) => `@${record.username}${record.role_name ? ` · ${record.role_name}` : ''} · ${formatDate(record.date)}`}
>
	{#snippet badge(record)}
		<Badge tone={STATUS_TONES[record.status]}>{STATUS_LABELS[record.status]}</Badge>
		{#if record.auto_closed}<Badge tone="neutral" title={attendanceListText.autoClosedHint}>{attendanceListText.autoClosed}</Badge>{/if}
	{/snippet}
	{#snippet body(record)}
		<Card flush>
			<div class="grid divide-y divide-slate-100 border-b border-slate-100 bg-brand-soft tablet:grid-cols-3 tablet:divide-x tablet:divide-y-0">
				<div class="p-4 tablet:p-5">
					<p class="text-xs text-slate-500">{attendanceListText.clockIn}</p>
					<p class="mt-0.5 text-xl font-semibold text-brand-ink">{record.clock_in_at ? formatTime(record.clock_in_at) : EMPTY_VALUE}</p>
				</div>
				<div class="p-4 tablet:p-5">
					<p class="text-xs text-slate-500">{attendanceListText.clockOut}</p>
					<p class="mt-0.5 text-xl font-semibold text-brand-ink">{record.clock_out_at ? formatTime(record.clock_out_at) : EMPTY_VALUE}</p>
				</div>
				<div class="p-4 tablet:p-5">
					<p class="text-xs text-slate-500">{attendanceListText.duration}</p>
					<p class="mt-0.5 text-xl font-semibold text-brand-ink">{formatDuration(record.work_minutes)}</p>
				</div>
			</div>
			<div class="grid laptop:grid-cols-[minmax(0,1fr)_minmax(0,1.4fr)]">
				<div class="border-b border-slate-100 p-4 tablet:p-5 laptop:border-b-0 laptop:border-r">
					<FigureList
						title={attendanceListText.details}
						figures={[
							{ label: termText.date, value: formatDate(record.date) },
							{ label: termText.status, value: STATUS_LABELS[record.status] },
							{ label: scheduleText.shiftCode, value: record.shift_code ?? EMPTY_VALUE },
							{ label: attendanceListText.late, value: record.late_minutes > 0 ? format(attendanceListText.lateMinutes, { minutes: record.late_minutes }) : EMPTY_VALUE },
							{ label: termText.discount, value: record.penalty > 0 ? formatRupiah(record.penalty) : EMPTY_VALUE },
							{ label: termText.note, value: record.note ?? EMPTY_VALUE }
						]}
					/>
				</div>
				<div class="flex flex-col gap-3 p-4 tablet:p-5">
					<span class="text-sm font-semibold text-slate-800">{attendanceListText.attendanceProof}</span>
					<div class="grid gap-4 tablet:grid-cols-2">
						{#each proofs(record) as item (item.side)}
							<figure class="flex flex-col gap-2">
								{#if item.proof.photo_url}
									<a href={item.proof.photo_url} target="_blank" rel="noopener" aria-label={format(attendanceListText.openPhotoNamed, { caption: item.caption })}>
										<img src={item.proof.photo_url} alt={format(attendanceListText.photoOfPerson, { caption: item.caption, name: record.name || record.username })} class="aspect-4/3 w-full rounded-lg border border-slate-200 object-cover" />
									</a>
								{:else}
									<div class="flex h-28 w-full flex-col items-center justify-center gap-1 rounded-lg border border-dashed border-slate-200 bg-slate-50 text-xs text-slate-500">
										<i class="ti ti-camera-off text-xl" aria-hidden="true"></i>
										{attendanceListText.noPhotoShown}
									</div>
								{/if}
								<figcaption class="flex flex-col gap-1">
									<span class="text-sm font-semibold text-slate-800">{item.caption}</span>
									<span class="text-xs text-slate-500">{item.at ? formatDateTime(item.at) : attendanceListText.notYet}</span>
									{#if item.proof.submitted_late || item.proof.needs_review}
										<span class="flex flex-wrap gap-1">
											{#if item.proof.submitted_late}<Badge tone="warning" title={attendanceListText.submittedLateHint}>{attendanceListText.submittedLate}</Badge>{/if}
											{#if item.proof.needs_review}<Badge tone="warning" title={attendanceListText.needsReviewHint}>{attendanceListText.needsReview}</Badge>{/if}
										</span>
										{#if item.proof.submitted_at}<span class="text-xs text-slate-500">{format(attendanceListText.receivedAt, { time: formatDateTime(item.proof.submitted_at) })}</span>{/if}
									{/if}
									{#if item.proof.latitude !== null && item.proof.longitude !== null}
										<span class="self-start"><Button label={item.proof.distance_meters !== null ? format(attendanceListText.metersFromBranch, { meters: Math.round(item.proof.distance_meters) }) : attendanceListText.viewMap} icon="map-pin" variant="tertiary" small onclick={() => (map = { record, side: item.side })} /></span>
									{/if}
								</figcaption>
							</figure>
						{/each}
					</div>
					{#if record.outside_schedule_reason}
						<div class="flex flex-col gap-1 border-t border-slate-100 pt-3">
							<Badge tone="warning" title={record.outside_schedule_reason}>{attendanceListText.offSchedule}</Badge>
							<span class="text-xs text-slate-600">{record.outside_schedule_reason}</span>
						</div>
					{/if}
				</div>
			</div>
		</Card>
		{#if map}
			<LocationDialog view={map} onclose={() => (map = null)} />
		{/if}
	{/snippet}
	{#snippet form(props)}
		<AttendanceEditForm record={props.record} busy={props.busy} error={props.error} fieldErrors={props.fieldErrors} onsave={props.onsave} onclose={props.onclose} />
	{/snippet}
	{#snippet removeNote(record)}
		<RichText template={attendanceListText.attendanceRemoveNote} values={{ name: record.name || record.username, date: formatDate(record.date) }} />
	{/snippet}
</RecordDetailView>
