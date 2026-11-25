<script lang="ts">
	import { goto } from '$app/navigation';
	import { onMount } from 'svelte';
	import { api } from '$lib/api';
	import { userMessage } from '$lib/api/user-message';
	import { clearSession, getUser } from '$lib/auth/session';
	import TextButton from '$lib/components/button/TextButton.svelte';
	import ConfirmDialog from '$lib/components/dialog/ConfirmDialog.svelte';
	import { unfold } from '$lib/motion/transitions';
	import { SIGN_IN_PATH } from '$lib/nav/pages';
	import { demoMode } from '$lib/stores/demo-mode.svelte';
	import { demoText } from '$lib/text/demo';

	// Server tetap menolak bila bukan pemilik; tombol hanya disembunyikan dari peran lain supaya tidak menawarkan yang pasti ditolak.
	const canExit = getUser()?.full_access === true;

	let confirming = $state(false);
	let busy = $state(false);
	let error = $state('');

	onMount(() => {
		// Halaman yang baru dibuka belum tentu sudah menerima respons berheader demo, jadi status dibaca sekali.
		api.demo
			.status()
			.then((status) => demoMode.set(status.active))
			.catch(() => {});
	});

	function ask(): void {
		error = '';
		confirming = true;
	}

	async function exit(): Promise<void> {
		busy = true;
		error = '';
		try {
			await api.demo.leave();
		} catch (failure) {
			error = userMessage(failure, demoText.exitFailed);
			return;
		} finally {
			busy = false;
		}
		confirming = false;
		demoMode.set(false);
		clearSession();
		await goto(SIGN_IN_PATH, { replaceState: true });
	}
</script>

{#if demoMode.active}
	<div transition:unfold class="shrink-0 border-b border-warning-200 bg-warning-50" role="status">
		<p class="flex flex-wrap items-center gap-x-3 gap-y-1 px-4 py-2 text-xs font-semibold text-warning-700 tablet:px-6">
			<i class="ti ti-flask text-base" aria-hidden="true"></i>
			{demoText.bar}
			{#if canExit}
				<TextButton label={demoText.exit} onclick={ask} />
			{/if}
		</p>
	</div>
{/if}

<ConfirmDialog open={confirming} title={demoText.exitTitle} confirmLabel={demoText.exitConfirm} {busy} {error} onconfirm={() => void exit()} oncancel={() => (confirming = false)}>
	{demoText.exitBody}
</ConfirmDialog>
