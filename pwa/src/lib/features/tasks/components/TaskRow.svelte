<script lang="ts">
	import TaskCard from '$lib/components/card/TaskCard.svelte';
	import { whenLabel } from '$lib/format/labels';
	import { t } from '$lib/text/t';
	import type { TaskItem } from '../tasks.svelte';

	const CAPTION_SEPARATOR = ' · ';

	/** Satu tugas karyawan sebagai kartu: cabang di keterangan, lalu waktu selesai atau batas waktunya; ketuk kartu atau tombolnya membuka rincian. */
	let { task, onclick }: { task: TaskItem; onclick: () => void } = $props();

	const timing = $derived(task.done ? (task.doneAt ? whenLabel(task.doneAt) : null) : task.due ? t('dashboard_task_due', whenLabel(task.due)) : null);
	const caption = $derived([task.outletName, timing].filter(Boolean).join(CAPTION_SEPARATOR) || null);
</script>

<TaskCard
	title={task.title}
	{caption}
	completed={task.done}
	tone="light"
	icon="Checklist"
	badge={task.mine ? { text: t('schedule_mine'), tone: 'positive' } : null}
	actionLabel={task.canComplete ? t('tasks_complete_submit') : null}
	onAction={onclick}
	{onclick}
/>
