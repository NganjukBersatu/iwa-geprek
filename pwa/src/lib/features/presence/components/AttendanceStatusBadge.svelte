<script lang="ts">
	import StatusBadge from '$lib/components/feedback/StatusBadge.svelte';
	import type { BadgeTone } from '$lib/components/feedback/types';
	import { t } from '$lib/text/t';
	import type { AttendanceDay } from '../presence.svelte';

	let { day }: { day: AttendanceDay } = $props();

	const look = $derived.by((): [string, BadgeTone] => {
		switch (day.status) {
			case 'present':
				return [t('status_present'), 'positive'];
			case 'late':
				return [t('status_late', String(day.lateMinutes)), 'warning'];
			case 'permit':
				return [t('status_permit'), 'neutral'];
			case 'sick':
				return [t('status_sick'), 'neutral'];
			default:
				return [t('status_absent'), 'danger'];
		}
	});
</script>

<StatusBadge text={look[0]} tone={look[1]} />
