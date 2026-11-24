<script lang="ts">
	import { api } from '$lib/api';
	import type { OptionMenu, VariantGroup, VariantGroupCreate } from '$lib/api/types';
	import { PAGES, variantGroupPath } from '$lib/nav/pages';
	import { createText } from '$lib/text/record-detail';
	import RecordCreateView from '../../record-detail/components/RecordCreateView.svelte';
	import { RecordCreateState } from '../../record-detail/record-create.svelte';
	import VariantGroupForm from './VariantGroupForm.svelte';

	const create = new RecordCreateState<VariantGroup, VariantGroupCreate, OptionMenu[]>({
		context: () => api.options.menus(),
		create: (body) => api.options.createGroup(body),
		name: (group) => group.name,
		after: (group) => variantGroupPath(group.id),
		text: createText('kelompok varian')
	});
</script>

<RecordCreateView {create} back={PAGES.options}>
	{#snippet form(props)}
		<VariantGroupForm group={null} menus={props.context ?? []} busy={props.busy} error={props.error} fieldErrors={props.fieldErrors} onsave={(body) => props.onsave(body as VariantGroupCreate)} onclose={props.onclose} />
	{/snippet}
</RecordCreateView>
