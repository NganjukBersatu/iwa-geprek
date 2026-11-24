<script lang="ts">
	import type { Snippet } from 'svelte';
	import PermissionGate from '$lib/components/sheet/PermissionGate.svelte';
	import type { PermissionGateItem } from '$lib/components/sheet/types';
	import { cameraProblemText } from '$lib/platform/camera';
	import { PERMISSION_KINDS, permissions, type PermissionKind, type PermissionReason } from '$lib/platform/permissions.svelte';
	import { t } from '$lib/text/t';

	const SUCCESS_HOLD_MILLIS = 1500;

	/** Menampilkan isi, dengan panel izin di atasnya selama ada izin yang belum diberikan; [clear] menyala bila tidak ada panel izin lagi, supaya lembar lain menunggu gilirannya. */
	let { children, clear = $bindable(false) }: { children: Snippet; clear?: boolean } = $props();

	const pending = $derived(PERMISSION_KINDS.filter((kind) => permissions.status[kind] !== 'granted'));
	const complete = $derived(pending.length === 0);

	$effect(() => {
		clear = permissions.loaded && complete && !open;
	});

	// Panel tetap ada saat tampilan sukses dan animasi keluarnya, tidak hilang seketika.
	let open = $state(false);
	let leaving = $state(false);
	let timer: ReturnType<typeof setTimeout> | undefined;

	$effect(() => {
		void permissions.refresh();
	});

	$effect(() => {
		if (!permissions.loaded) return;
		clearTimeout(timer);
		if (!complete) {
			open = true;
			leaving = false;
		} else if (open) {
			timer = setTimeout(() => (leaving = true), SUCCESS_HOLD_MILLIS);
		}
		return () => clearTimeout(timer);
	});

	const copy: Record<PermissionKind, [string, string]> = {
		location: [t('permission_location_title'), t('permission_location_description')],
		camera: [t('permission_camera_title'), t('permission_camera_description')],
		gps: [t('permission_gps_title'), t('permission_gps_description')]
	};

	// Setelah dicoba dan gagal, keterangan berganti menjadi penyebab beserta langkah perbaikannya.
	function reasonText(kind: PermissionKind, reason: PermissionReason): string {
		switch (reason) {
			case 'denied':
				return kind === 'camera' ? cameraProblemText('denied') : t('web_permission_location_blocked');
			case 'timeout':
				return t('web_permission_timeout');
			case 'serviceOff':
				return t('web_permission_gps_blocked');
			case 'unanswered':
				return t('web_permission_unanswered');
			default:
				return cameraProblemText(reason);
		}
	}

	const items = $derived<PermissionGateItem[]>(
		PERMISSION_KINDS.map((kind) => {
			const granted = permissions.status[kind] === 'granted';
			const isGps = kind === 'gps';
			const reason = permissions.reason[kind];
			return {
				title: copy[kind][0],
				description: reason ? reasonText(kind, reason) : copy[kind][1],
				statusText: granted ? (isGps ? t('permission_status_on') : t('permission_status_granted')) : isGps ? t('permission_status_off') : t('permission_status_denied'),
				tone: granted ? 'positive' : 'warning',
				onclick: granted ? null : () => void permissions.request([kind])
			};
		})
	);
</script>

{@render children()}

{#if open}
	<PermissionGate
		title={t('permission_title')}
		message={t('permission_message')}
		{items}
		actionLabel={t('permission_action_allow')}
		onAction={() => void permissions.request(pending)}
		loading={permissions.checking}
		footnote={permissions.reference ? t('web_permission_help', permissions.reference) : ''}
		onClosed={() => {
			open = false;
			leaving = false;
		}}
		visible={!leaving}
		completed={complete}
		completedTitle={t('permission_success_title')}
		completedMessage={t('permission_success_message')}
	/>
{/if}
