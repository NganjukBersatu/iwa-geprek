<script lang="ts">
	import Banner from '$lib/components/card/Banner.svelte';
	import Button from '$lib/components/button/Button.svelte';
	import Notice from '$lib/components/card/Notice.svelte';
	import Modal from '$lib/components/dialog/Modal.svelte';
	import SelectField from '$lib/components/form/SelectField.svelte';
	import { actionText } from '$lib/text/actions';
	import { format } from '$lib/text/format';
	import { stationText } from '$lib/text/stations';
	import { termText } from '$lib/text/terms';
	import { DIRECT, DIRECT_LABEL, type SetupState } from '../setup.svelte';

	let { setup }: { setup: SetupState } = $props();

	const form = $derived(setup.form);
	const categories = $derived((setup.data?.categories ?? []).map((category) => ({ value: category.id, label: category.name })));
	const stations = $derived([
		{ value: DIRECT, label: DIRECT_LABEL },
		...(setup.data?.stations ?? []).filter((station) => station.kind === 'make').map((station) => ({ value: station.id, label: station.name }))
	]);
	const branches = $derived(form ? setup.branchesFor(form.categoryId, form.outletId) : []);
	const categoryName = $derived(categories.find((category) => category.value === form?.categoryId)?.label ?? '');
	const outletName = $derived(setup.outlets.find((outlet) => outlet.id === form?.outletId)?.name ?? '');
	const title = $derived(
		form?.mode === 'add'
			? stationText.addBranchRow
			: form?.outletId
				? format(stationText.routeEditInBranch, { category: categoryName, branch: outletName })
				: format(stationText.routeEditAll, { category: categoryName })
	);
</script>

<Modal
	open={form !== null}
	{title}
	description={form?.mode === 'add' ? stationText.routeAddDescription : undefined}
	size="sm"
	busy={setup.busy}
	onclose={() => setup.closeDialogs()}
>
	{#if form}
		<div class="flex flex-col gap-3">
			{#if form.mode === 'add'}
				<SelectField label={termText.category} options={categories} bind:value={form.categoryId} onchange={() => (form.outletId = null)} />
				{#if branches.length === 0}
					<Notice text={stationText.allBranchesHaveRoute} />
				{:else}
					<SelectField label={termText.branch} options={branches} empty={stationText.chooseBranchPrompt} value={form.outletId ?? ''} onchange={(value) => (form.outletId = value || null)} />
				{/if}
			{/if}
			<SelectField label={termText.station} options={stations} bind:value={form.stationId} />
			{#if setup.actionError}<Banner tone="danger" icon="alert-triangle">{setup.actionError}</Banner>{/if}
		</div>
	{/if}

	{#snippet footer()}
		<Button label={actionText.cancel} disabled={setup.busy} onclick={() => setup.closeDialogs()} />
		<Button label={setup.busy ? actionText.saving : actionText.save} variant="primary" disabled={setup.busy} onclick={() => void setup.saveForm()} />
	{/snippet}
</Modal>
