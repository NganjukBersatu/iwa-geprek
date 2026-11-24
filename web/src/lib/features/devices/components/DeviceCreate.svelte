<script lang="ts">
	import { goto } from '$app/navigation';
	import { api } from '$lib/api';
	import type { DeviceCode, DeviceCreate as DeviceInput } from '$lib/api/types';
	import { ApiError } from '$lib/api/http';
	import { userMessage } from '$lib/api/user-message';
	import { PAGES } from '$lib/nav/pages';
	import DeviceCodeDialog from './DeviceCodeDialog.svelte';
	import DeviceForm from './DeviceForm.svelte';
	import { deviceText } from '$lib/text/devices';

	let busy = $state(false);
	let error = $state('');
	let fieldErrors = $state<Record<string, string>>({});
	let issued = $state<DeviceCode | null>(null);

	async function save(body: object, outletId: string): Promise<void> {
		busy = true;
		error = '';
		fieldErrors = {};
		try {
			issued = await api.devices.create(outletId, body as DeviceInput);
		} catch (cause) {
			fieldErrors = cause instanceof ApiError ? cause.fieldErrors : {};
			error = userMessage(cause, deviceText.saveFailed);
		} finally {
			busy = false;
		}
	}
</script>

<DeviceForm device={null} {busy} {error} {fieldErrors} onsave={(body, outletId) => void save(body, outletId)} onclose={() => void goto(PAGES.devices.path)} />

{#if issued}
	<DeviceCodeDialog {issued} onclose={() => void goto(PAGES.devices.path)} />
{/if}
