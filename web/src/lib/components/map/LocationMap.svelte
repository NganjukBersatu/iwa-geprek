<script lang="ts">
	import { userMessage } from '$lib/api/user-message';
	import type { Map as LeafletMap } from 'leaflet';
	import { onMount } from 'svelte';
	import { controlText } from '$lib/text/controls';

	let {
		latitude,
		longitude,
		accuracy = 0,
		branchLatitude = null,
		branchLongitude = null,
		radius = 50
	}: {
		latitude: number;
		longitude: number;
		accuracy?: number;
		branchLatitude?: number | null;
		branchLongitude?: number | null;
		radius?: number;
	} = $props();

	const START_ZOOM = 18;
	const MAX_ZOOM = 19;
	const FIT_PADDING = 24;
	const TILES = 'https://tile.openstreetmap.org/{z}/{x}/{y}.png';

	let container = $state<HTMLDivElement | null>(null);
	let problem = $state('');
	let map: LeafletMap | null = null;

	const token = (name: string) => getComputedStyle(document.documentElement).getPropertyValue(name).trim();

	onMount(() => {
		let cancelled = false;
		void (async () => {
			try {
				const [{ default: L }] = await Promise.all([import('leaflet'), import('leaflet/dist/leaflet.css')]);
				const [icon, icon2x, shadow] = await Promise.all([
					import('leaflet/dist/images/marker-icon.png?url'),
					import('leaflet/dist/images/marker-icon-2x.png?url'),
					import('leaflet/dist/images/marker-shadow.png?url')
				]);
				L.Icon.Default.mergeOptions({ iconUrl: icon.default, iconRetinaUrl: icon2x.default, shadowUrl: shadow.default });
				if (cancelled || !container) return;

				const danger = token('--color-danger-500');
				const brand = token('--color-brand');
				const view = L.map(container).setView([latitude, longitude], START_ZOOM);
				map = view;
				L.tileLayer(TILES, { maxZoom: MAX_ZOOM, attribution: '&copy; OpenStreetMap contributors' }).addTo(view);

				L.circleMarker([latitude, longitude], { radius: 8, color: danger, fillColor: danger, fillOpacity: 0.9 }).addTo(view).bindPopup(controlText.attendanceLocation);
				const bounds = [L.latLng(latitude, longitude)];
				if (accuracy > 0) {
					const circle = L.circle([latitude, longitude], { radius: accuracy, color: danger, weight: 1, fillOpacity: 0.1 }).addTo(view);
					bounds.push(circle.getBounds().getNorthEast(), circle.getBounds().getSouthWest());
				}
				if (branchLatitude !== null && branchLongitude !== null) {
					L.marker([branchLatitude, branchLongitude]).addTo(view).bindPopup(controlText.branchPoint);
					const circle = L.circle([branchLatitude, branchLongitude], { radius, color: brand, weight: 2, fillOpacity: 0.12 }).addTo(view);
					bounds.push(circle.getBounds().getNorthEast(), circle.getBounds().getSouthWest());
				}
				view.fitBounds(L.latLngBounds(bounds), { padding: [FIT_PADDING, FIT_PADDING], maxZoom: MAX_ZOOM });
			} catch (error) {
				problem = userMessage(error, controlText.mapLoadFailed);
			}
		})();
		return () => {
			cancelled = true;
			map?.remove();
		};
	});
</script>

{#if problem}
	<p class="rounded-lg border border-danger-200 bg-danger-50 px-3 py-2 text-sm text-danger-700" role="alert">{problem}</p>
{/if}
<div bind:this={container} class="h-72 w-full overflow-hidden rounded-lg border border-slate-200 tablet:h-96"></div>
