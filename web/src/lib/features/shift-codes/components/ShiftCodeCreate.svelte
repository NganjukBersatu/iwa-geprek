<script lang="ts">
	import { api } from '$lib/api';
	import type { CodeGroup, CodeGroupCreate } from '$lib/api/types';
	import { PAGES, shiftCodePath } from '$lib/nav/pages';
	import { branchList } from '$lib/stores/branch';
	import { createText } from '$lib/text/record-detail';
	import RecordCreateView from '../../record-detail/components/RecordCreateView.svelte';
	import { RecordCreateState } from '../../record-detail/record-create.svelte';
	import ShiftCodeForm from './ShiftCodeForm.svelte';

	type ShiftContext = { outlets: { id: string; name: string }[]; categories: string[] };

	const create = new RecordCreateState<CodeGroup, CodeGroupCreate, ShiftContext>({
		context: async () => {
			const [outlets, categories] = await Promise.all([branchList(), api.shiftCodes.categories()]);
			return { outlets, categories };
		},
		create: (body) => api.shiftCodes.create(body),
		name: (group) => group.code,
		after: (group) => shiftCodePath(group.id),
		text: createText('kode shift')
	});
</script>

<RecordCreateView {create} back={PAGES.shiftCodes}>
	{#snippet form(props)}
		<ShiftCodeForm group={null} outlets={props.context?.outlets ?? []} categories={props.context?.categories ?? []} busy={props.busy} error={props.error} fieldErrors={props.fieldErrors} onsave={(body) => props.onsave(body as CodeGroupCreate)} onclose={props.onclose} />
	{/snippet}
</RecordCreateView>
