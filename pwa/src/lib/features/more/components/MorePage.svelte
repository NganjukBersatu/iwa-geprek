<script lang="ts">
	import { dynamicStyle } from '$lib/platform/dynamic-style';
	import CardGrid from '$lib/components/card/CardGrid.svelte';
	import FeatureCard from '$lib/components/card/FeatureCard.svelte';
	import type { CardTone } from '$lib/components/card/types';
	import type { IconName } from '$lib/theme/icons';
	import { t } from '$lib/text/t';

	type MoreCard = { href: string; title: string; icon: IconName; decoration: IconName; tone: CardTone };

	/** Urutan kartu Lainnya, dua kolom: baris pertama Tugas dan Kinerja, lalu Kehadiran dan Izin & Lembur, Riwayat dan Prosedur Kerja, terakhir Info Aplikasi di tengah. */
	const cards: MoreCard[] = [
		{ href: '/tasks', title: t('nav_tasks'), icon: 'Checklist', decoration: 'ClipboardCheck', tone: 'primary' },
		{ href: '/performance', title: t('nav_performance'), icon: 'Dashboard', decoration: 'ChartLine', tone: 'deep' },
		{ href: '/presence?from=more', title: t('nav_presence'), icon: 'Calendar', decoration: 'CalendarCheck', tone: 'soft' },
		{ href: '/leave-overtime', title: t('nav_leave_overtime'), icon: 'Briefcase', decoration: 'Moon', tone: 'primary' },
		{ href: '/activity', title: t('nav_activity'), icon: 'History', decoration: 'ClipboardList', tone: 'accent' },
		{ href: '/sop', title: t('nav_sop'), icon: 'Book', decoration: 'FileText', tone: 'soft' },
		{ href: '/about', title: t('nav_info'), icon: 'Info', decoration: 'HelpCircle', tone: 'primary' }
	];
</script>

<div class="flex size-full justify-center" use:dynamicStyle={{ 'padding-inline': 'var(--page-padding)' }}>
	<div class="size-full max-w-[var(--size-content-max)]" use:dynamicStyle={{ 'padding-block': '8px' }}>
		<CardGrid items={cards}>
			{#snippet card(item)}
				<FeatureCard {...item} />
			{/snippet}
		</CardGrid>
	</div>
</div>
