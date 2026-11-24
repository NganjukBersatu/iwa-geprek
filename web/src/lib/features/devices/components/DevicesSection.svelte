<script lang="ts">
	import ManageSection from '$lib/features/manage/ManageSection.svelte';
	import { deviceText } from '$lib/text/devices';
	import { DevicesState } from '../devices.svelte';
	import DevicesView from './DevicesView.svelte';

	/** Perangkat satu cabang di halaman detail cabang; cabangnya dibaca dari pilihan cabang yang sudah ditetapkan halaman itu. */
	const devices = new DevicesState();
</script>

<ManageSection manage={devices} loadingText={deviceText.loading}>
	<DevicesView {devices} />
</ManageSection>
