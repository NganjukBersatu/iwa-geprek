<script lang="ts">
	import { untrack } from 'svelte';
	import { api } from '$lib/api';
	import type { Batch, BatchInput } from '$lib/api/types';
	import { PAGES, batchPath } from '$lib/nav/pages';
	import { batchText } from '$lib/text/batches';
	import { createText } from '$lib/text/record-detail';
	import RecordCreateView from '../../record-detail/components/RecordCreateView.svelte';
	import { RecordCreateState } from '../../record-detail/record-create.svelte';
	import type { BatchKind } from '../constants';
	import BatchForm from './BatchForm.svelte';

	let { kind }: { kind: BatchKind } = $props();

	type BatchSave = { body: BatchInput; outletId: string };

	const create = new RecordCreateState<Batch, BatchSave>({
		create: ({ body, outletId }) => api.batches.create(outletId, body),
		name: (batch) => batch.name,
		after: (batch) => batchPath(batch.id),
		text: createText(batchText.kinds[untrack(() => kind)].noun)
	});
</script>

<RecordCreateView {create} back={PAGES.tasks}>
	{#snippet form(props)}
		<BatchForm {kind} batch={null} busy={props.busy} error={props.error} fieldErrors={props.fieldErrors} onsave={(body, outletId) => props.onsave({ body, outletId })} onclose={props.onclose} />
	{/snippet}
</RecordCreateView>
