<script lang="ts">
	import ShiftRow from '$lib/components/card/ShiftRow.svelte';
	import { durationLabel, timeRange } from '$lib/format/labels';
	import { spanMinutes } from '$lib/format/datetime';
	import { parseHexColor } from '$lib/theme/hex';
	import { t } from '$lib/text/t';
	import type { ScheduleItem } from '../schedule.svelte';

	/** Satu penugasan jadwal; [showUser] menjadikan nama staf judulnya dan jam di keterangan. */
	let { item, showUser }: { item: ScheduleItem; showUser: boolean } = $props();

	const code = $derived(item.code);
	const hours = $derived(item.off ? t('schedule_day_off') : code?.start && code.end ? timeRange(code.start, code.end) : (code?.code ?? ''));
	const role = $derived(item.roleName ? t('schedule_as_role', item.roleName) : null);
	const note = $derived(item.note?.trim() ? item.note : null);
	const session = $derived(code?.category ? t('format_detail_pair', code.category, hours) : hours);
	const caption = $derived(note ? t('format_detail_pair', session, note) : session);
	const overtime = $derived(
		!item.off && code?.overtimeStart && code.overtimeEnd
			? t('schedule_overtime_total', timeRange(code.overtimeStart, code.overtimeEnd), durationLabel(spanMinutes(code.overtimeStart, code.overtimeEnd)))
			: null
	);
</script>

<ShiftRow
	title={showUser ? item.userName : session}
	detail={role}
	caption={showUser ? caption : note}
	footnote={overtime}
	code={code?.code}
	codeColor={parseHexColor(code?.color)}
	tag={showUser && item.mine ? t('schedule_mine') : null}
/>
