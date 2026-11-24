<script lang="ts">
	import { untrack } from 'svelte';
	import { api } from '$lib/api';
	import type { Announcement, AnnouncementUpdate } from '$lib/api/types';
	import Button from '$lib/components/button/Button.svelte';
	import Badge from '$lib/components/card/Badge.svelte';
	import Card from '$lib/components/card/Card.svelte';
	import FigureGrid from '$lib/components/card/FigureGrid.svelte';
	import { formatDate } from '$lib/date/range';
	import { scopeText } from '$lib/components/form/branch-prices.svelte';
	import { branches } from '$lib/stores/branch';
	import { PAGES } from '$lib/nav/pages';
	import { recordText } from '$lib/text/record-detail';
	import RecordDetailView from '../../record-detail/components/RecordDetailView.svelte';
	import { RecordDetailState } from '../../record-detail/record-detail.svelte';
	import { STATUS_LABELS, STATUS_TONES } from '../labels';
	import AnnouncementForm from './AnnouncementForm.svelte';
	import { termText } from '$lib/text/terms';
	import { promotionText } from '$lib/text/promotions';
	import { format } from '$lib/text/format';

	type AnnouncementSave = { body: AnnouncementUpdate; image: File | null };

	let { id }: { id: string } = $props();

	const detail = new RecordDetailState<Announcement, AnnouncementSave, null>(untrack(() => id), {
		load: (announcementId) => api.promotions.announcement(announcementId),
		update: async (announcement, { body, image }) => {
			const saved = await api.promotions.updateAnnouncement(announcement.id, body);
			return image ? api.promotions.uploadImage(saved.id, image) : saved;
		},
		remove: (announcement) => api.promotions.removeAnnouncement(announcement.id),
		name: (announcement) => announcement.title,
		text: recordText('promosi', PAGES.promotions.label)
	});
</script>

<RecordDetailView {detail} back={PAGES.promotions} trail={(announcement) => [{ label: PAGES.promotions.label, href: PAGES.promotions.path }, { label: announcement.title }]} tables={['cafe_promotions']} title={(announcement) => announcement.title} description={() => promotionText.announcementsDescription}>
	{#snippet badge(announcement)}
		<Badge tone={STATUS_TONES[announcement.status]}>{STATUS_LABELS[announcement.status]}</Badge>
	{/snippet}
	{#snippet extraActions(announcement)}
		<Button
			label={announcement.is_active ? promotionText.deactivate : promotionText.activate}
			icon={announcement.is_active ? 'player-pause' : 'player-play'}
			variant="tertiary"
			disabled={detail.busy}
			onclick={() => void detail.change((current) => api.promotions.updateAnnouncement(current.id, { is_active: !current.is_active }), promotionText.announcementStatusChangeFailed)}
		/>
	{/snippet}
	{#snippet body(announcement)}
		<Card flush>
			<div class="p-4 tablet:p-5">
				<FigureGrid
					label={promotionText.announcementSummary}
					figures={[
						{ label: promotionText.title, value: announcement.title },
						{ label: termText.branch, value: scopeText(announcement.outlet_id, $branches) },
						{ label: termText.status, value: STATUS_LABELS[announcement.status] ?? announcement.status },
						{ label: promotionText.from, value: formatDate(announcement.starts_on) },
						{ label: promotionText.until, value: formatDate(announcement.ends_on) }
					]}
				/>
			</div>
			<section class="flex flex-col gap-2 border-t border-slate-100 p-4 tablet:p-5">
				<h3 class="text-sm font-semibold text-slate-800">{termText.description}</h3>
				<p class="whitespace-pre-line text-xs text-slate-700">{announcement.description}</p>
			</section>
			<section class="flex flex-col gap-2 border-t border-slate-100 p-4 tablet:p-5">
				<h3 class="text-sm font-semibold text-slate-800">{promotionText.image}</h3>
				{#if announcement.image_url}
					<img src={announcement.image_url} alt={format(promotionText.imageOf, { name: announcement.title })} class="max-h-48 w-fit rounded-lg border border-slate-200 bg-white object-contain p-1" />
				{:else}
					<p class="text-xs text-slate-500">{promotionText.noImage}</p>
				{/if}
			</section>
		</Card>
	{/snippet}
	{#snippet form(props)}
		<AnnouncementForm announcement={props.record} busy={props.busy} error={props.error} fieldErrors={props.fieldErrors} onsave={(body, image) => props.onsave({ body: body as AnnouncementUpdate, image })} onclose={props.onclose} />
	{/snippet}
	{#snippet removeNote()}
		{promotionText.announcementRemoveNote}
	{/snippet}
</RecordDetailView>
