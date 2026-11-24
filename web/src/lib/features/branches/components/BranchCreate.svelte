<script lang="ts">
	import { api } from '$lib/api';
	import type { Branch, BranchCreate } from '$lib/api/types';
	import { PAGES, branchPath } from '$lib/nav/pages';
	import { createText } from '$lib/text/record-detail';
	import RecordCreateView from '../../record-detail/components/RecordCreateView.svelte';
	import { RecordCreateState } from '../../record-detail/record-create.svelte';
	import BranchForm from './BranchForm.svelte';

	const create = new RecordCreateState<Branch, BranchCreate>({
		create: (body) => api.branches.create(body),
		name: (branch) => branch.name,
		after: (branch) => branchPath(branch.id),
		text: createText('cabang')
	});
</script>

<RecordCreateView {create} back={PAGES.branches}>
	{#snippet form(props)}
		<BranchForm branch={null} busy={props.busy} error={props.error} fieldErrors={props.fieldErrors} onsave={(body) => props.onsave(body as BranchCreate)} onclose={props.onclose} />
	{/snippet}
</RecordCreateView>
