<script lang="ts">
	import type { IconName } from '$lib/theme/icons';
	import TaskCard from './TaskCard.svelte';

	/** Kartu tugas rutin (warna teks) atau tugas outlet (warna utama) di atas TaskCard: setelah selesai judulnya [doneLabel] dan tombolnya membuka pilihan perbaiki atau hapus; [note] menyebut siapa yang mengisi tugas rutin. */
	let {
		title,
		rangeLabel,
		completed,
		tone = 'green',
		icon = 'UsersGroup',
		note = null,
		tagLabel,
		fillLabel,
		doneLabel,
		manageLabel,
		onFill,
		onManage
	}: {
		title: string;
		rangeLabel: string;
		completed: boolean;
		tone?: 'green' | 'tan';
		icon?: IconName;
		note?: string | null;
		tagLabel: string;
		fillLabel: string;
		doneLabel: string;
		manageLabel: string;
		onFill: () => void;
		/** Membuka pilihan untuk pengisian yang sudah dikirim; tanpa ini kartu selesai tidak punya tombol. */
		onManage?: () => void;
	} = $props();
</script>

{#if completed}
	<TaskCard title={doneLabel} caption={`${title} · ${rangeLabel}`} completed {tone} {icon} actionLabel={onManage ? manageLabel : null} onAction={onManage} onclick={onManage} />
{:else}
	<TaskCard
		{title}
		caption={note ? `${rangeLabel} · ${note}` : rangeLabel}
		completed={false}
		{tone}
		{icon}
		badge={{ text: tagLabel, tone: tone === 'green' ? 'strong' : 'accent' }}
		actionLabel={fillLabel}
		onAction={onFill}
	/>
{/if}
