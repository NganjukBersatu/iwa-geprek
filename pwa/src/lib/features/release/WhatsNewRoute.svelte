<script lang="ts">
	import NoticeSheet from '$lib/components/sheet/NoticeSheet.svelte';
	import { t } from '$lib/text/t';
	import { PWA_RELEASE } from './release';
	import { WhatsNewState } from './whats-new.svelte';

	// Ringkasan pembaruan tampil sekali per akun sebelum pemberitahuan lain, supaya dua lembar tidak bertumpuk.
	let { onSessionExpired, done = $bindable(false) }: { onSessionExpired: () => void; done?: boolean } = $props();

	const whatsNew = new WhatsNewState();

	$effect(() => {
		void whatsNew.load(onSessionExpired);
	});

	$effect(() => {
		done = whatsNew.settled && !whatsNew.open;
	});
</script>

{#if whatsNew.open}
	<NoticeSheet
		title={t('release_title', PWA_RELEASE.version)}
		items={PWA_RELEASE.notes.map((note) => ({ title: t(note.key), caption: null, icon: note.icon }))}
		closeLabel={t('notices_close')}
		onClose={() => whatsNew.close()}
	/>
{/if}
