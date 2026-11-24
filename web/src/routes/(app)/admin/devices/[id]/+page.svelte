<script lang="ts">
	import { page } from '$app/state';
	import DeviceDetail from '$lib/features/devices/components/DeviceDetail.svelte';
</script>

<DeviceDetail id={page.params['id'] as string} />
