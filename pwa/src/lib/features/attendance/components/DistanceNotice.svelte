<script lang="ts">
	import SecondaryButton from '$lib/components/button/SecondaryButton.svelte';
	import Notice from '$lib/components/feedback/Notice.svelte';
	import { t } from '$lib/text/t';
	import type { AttendanceBranch } from '../models';

	/** Jarak ke cabang sebelum memotret; tidak tampil bila cabang tanpa titik atau radius. */
	let {
		branch,
		distance,
		blocking,
		locating,
		located,
		locationProblem,
		onRelocate
	}: {
		branch: AttendanceBranch | null;
		distance: number | null;
		blocking: boolean;
		locating: boolean;
		located: boolean;
		locationProblem: string | null;
		onRelocate: () => void;
	} = $props();

	const radius = $derived(branch?.radiusMeters ?? null);
	const text = $derived.by(() => {
		if (!branch || radius === null || branch.latitude === null || branch.longitude === null) return null;
		if (locating) return t('attendance_distance_locating');
		if (distance === null) return located ? (locationProblem ?? t('attendance_location_unavailable')) : null;
		const meters = String(Math.round(distance));
		return blocking
			? t('attendance_distance_outside', meters, branch.name, String(radius))
			: t('attendance_distance_inside', meters, branch.name, String(radius));
	});
</script>

{#if text}
	<div class="flex w-full flex-col gap-2 pb-3">
		<Notice {text} />
		{#if !locating}
			<SecondaryButton text={t('attendance_distance_refresh')} onclick={onRelocate} />
		{/if}
	</div>
{/if}
