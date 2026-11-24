<script lang="ts">
	import { page } from '$app/state';
	import SopEditorView from '$lib/features/sop/components/SopEditorView.svelte';
	import { SopDraftState } from '$lib/features/sop/sop-draft.svelte';

	const draft = new SopDraftState(page.params['id'] as string);
</script>

<SopEditorView {draft} />
