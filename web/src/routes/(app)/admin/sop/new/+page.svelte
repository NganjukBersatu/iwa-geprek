<script lang="ts">
	import { replaceState } from '$app/navigation';
	import { page } from '$app/state';
	import SopEditorView from '$lib/features/sop/components/SopEditorView.svelte';
	import { SopDraftState } from '$lib/features/sop/sop-draft.svelte';
	import { SOP_DRAFT_PARAM, sopDraftPath } from '$lib/nav/pages';

	// Once the first draft is written its id goes into the address, so a reload or a later visit continues the same draft.
	const draft = new SopDraftState(null, page.url.searchParams.get(SOP_DRAFT_PARAM), (id) => replaceState(sopDraftPath(id), {}));
</script>

<SopEditorView {draft} />
