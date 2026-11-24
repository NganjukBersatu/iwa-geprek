<script lang="ts">
	import Banner from '$lib/components/card/Banner.svelte';
	import Modal from '$lib/components/dialog/Modal.svelte';
	import LocationMap from '$lib/components/map/LocationMap.svelte';
	import type { MapView } from '../attendance-list.svelte';
	import { attendanceListText } from '$lib/text/attendance-list';
	import { format } from '$lib/text/format';

	let { view, onclose }: { view: MapView; onclose: () => void } = $props();

	const OUTSIDE_MODE = 'luar';
	const proof = $derived(view.side === 'in' ? view.record.clock_in : view.record.clock_out);
	const where = $derived(view.side === 'in' ? 'datang' : 'pulang');
	const branch = $derived(view.record.branch_location);
</script>

<Modal open title={format(attendanceListText.locationTitle, { kind: where, name: view.record.name || view.record.username })} size="md" {onclose}>
	{#if proof.latitude !== null && proof.longitude !== null}
		<p class="mb-3 text-xs text-slate-500">
			{#if proof.distance_meters !== null}{format(attendanceListText.metersFromPoint, { meters: Math.round(proof.distance_meters) })}{#if proof.radius_meters !== null} {format(attendanceListText.radiusLimit, { meters: proof.radius_meters })}{/if} ·{/if}
			{format(attendanceListText.accuracyMeters, { meters: Math.round(proof.accuracy_meters ?? 0) })}
		</p>
		{#if proof.mode === OUTSIDE_MODE}
			<div class="mb-3"><Banner tone="warning" icon="alert-triangle" title={attendanceListText.outsideLocation}>{proof.note ?? attendanceListText.outsideRadiusNote}</Banner></div>
		{/if}
		{#if !branch}
			<p class="mb-3 text-xs text-slate-500">{attendanceListText.branchPointNotSet}</p>
		{/if}
		{#key view}
			<LocationMap latitude={proof.latitude} longitude={proof.longitude} accuracy={proof.accuracy_meters ?? 0} branchLatitude={branch?.latitude ?? null} branchLongitude={branch?.longitude ?? null} radius={proof.radius_meters ?? 50} />
		{/key}
	{/if}
</Modal>
