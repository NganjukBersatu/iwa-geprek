<script lang="ts">
	import { api } from '$lib/api';
	import type { Announcement, AnnouncementCreate } from '$lib/api/types';
	import { PAGES, announcementPath } from '$lib/nav/pages';
	import { createText } from '$lib/text/record-detail';
	import RecordCreateView from '../../record-detail/components/RecordCreateView.svelte';
	import { RecordCreateState } from '../../record-detail/record-create.svelte';
	import AnnouncementForm from './AnnouncementForm.svelte';

	type AnnouncementSave = { body: AnnouncementCreate; image: File | null };

	const create = new RecordCreateState<Announcement, AnnouncementSave>({
		create: async ({ body, image }) => {
			const saved = await api.promotions.createAnnouncement(body);
			return image ? api.promotions.uploadImage(saved.id, image) : saved;
		},
		name: (announcement) => announcement.title,
		after: (announcement) => announcementPath(announcement.id),
		text: createText('promosi')
	});
</script>

<RecordCreateView {create} back={PAGES.promotions}>
	{#snippet form(props)}
		<AnnouncementForm announcement={null} busy={props.busy} error={props.error} fieldErrors={props.fieldErrors} onsave={(body, image) => props.onsave({ body: body as AnnouncementCreate, image })} onclose={props.onclose} />
	{/snippet}
</RecordCreateView>
