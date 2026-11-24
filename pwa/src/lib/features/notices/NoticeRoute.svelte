<script lang="ts">
	import NoticeSheet from '$lib/components/sheet/NoticeSheet.svelte';
	import { whenLabel } from '$lib/format/labels';
	import { t } from '$lib/text/t';
	import { NoticesState, type NoticeItem } from './notices.svelte';

	/** Lembar pengumuman yang muncul sendiri setelah masuk bila ada yang perlu disampaikan. */
	let { onSessionExpired }: { onSessionExpired: () => void } = $props();

	const notices = new NoticesState();

	$effect(() => {
		void notices.load(onSessionExpired);
	});

	function text(item: NoticeItem): string {
		if (item.kind === 'task-overdue') return t('notice_task_overdue', item.title);
		if (item.kind === 'due-changed') return t('notice_due_changed', item.title);
		return t('notice_task_assigned', item.title);
	}
</script>

{#if notices.items.length > 0}
	<NoticeSheet
		title={t('notices_title')}
		items={notices.items.map((item) => ({ title: text(item), caption: item.showAt ? whenLabel(item.showAt) : null }))}
		closeLabel={t('notices_close')}
		onClose={() => notices.close()}
	/>
{/if}
