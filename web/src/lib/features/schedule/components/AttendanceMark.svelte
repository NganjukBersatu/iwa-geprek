<script lang="ts">
	import type { AttendanceRecord } from '$lib/api/types';
	import Badge from '$lib/components/card/Badge.svelte';
	import { formatTime } from '$lib/format/datetime';
	import { STATUS_LABELS, STATUS_TONES } from '../../attendance-list/labels';
	import { scheduleText } from '$lib/text/schedule';
	import { format } from '$lib/text/format';

	let { record }: { record: AttendanceRecord | undefined } = $props();
</script>

{#if record}
	<Badge tone={STATUS_TONES[record.status]} title={record.clock_in_at ? format(scheduleText.clockedInAt, { time: formatTime(record.clock_in_at), leaving: record.clock_out_at ? `, pulang ${formatTime(record.clock_out_at)}` : ', belum pulang' }) : undefined}>
		{STATUS_LABELS[record.status]}{#if record.clock_in_at}<span class="font-normal"> {formatTime(record.clock_in_at)}</span>{/if}
	</Badge>
{/if}
