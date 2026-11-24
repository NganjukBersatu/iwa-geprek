<script lang="ts">
	import { untrack } from 'svelte';
	import type { MenuItem } from '$lib/api/types';
	import Button from '$lib/components/button/Button.svelte';
	import Banner from '$lib/components/card/Banner.svelte';
	import Modal from '$lib/components/dialog/Modal.svelte';
	import MoneyField from '$lib/components/form/MoneyField.svelte';
	import { rupiahDigits, rupiahInput } from '$lib/format/currency';
	import { actionText } from '$lib/text/actions';
	import { format } from '$lib/text/format';
	import { menuDetailText } from '$lib/text/menu-detail';
	import type { MenuDetailState } from '../menu-detail.svelte';

	let { menu, item }: { menu: MenuDetailState; item: MenuItem } = $props();

	const text = menuDetailText.fixedCost;
	const saved = untrack(() => menu.fixedCost);
	let base = $state(saved ? rupiahInput(saved.cost ?? '') : '');
	let own = $state<Record<string, string>>(
		Object.fromEntries(untrack(() => menu.sellers).map((branch) => [branch.id, saved?.branch_costs[branch.id] !== undefined ? rupiahInput(saved.branch_costs[branch.id] ?? '') : '']))
	);
	let problem = $state('');

	function submit(): void {
		problem = '';
		if (rupiahDigits(base) === '') {
			problem = text.baseRequired;
			return;
		}
		const branchCosts: Record<string, string | null> = {};
		for (const branch of menu.sellers) {
			const digits = rupiahDigits(own[branch.id] ?? '');
			branchCosts[branch.id] = digits === '' ? null : digits;
		}
		void menu.saveFixedCost({ cost: rupiahDigits(base), branch_costs: branchCosts });
	}
</script>

<Modal open title={format(item.has_fixed_cost ? text.editTitle : text.newTitle, { name: item.name })} description={text.dialogDescription} size="md" busy={menu.busy} onclose={() => menu.closeDialogs()}>
	<div class="flex flex-col gap-4">
		<MoneyField label={text.baseLabel} bind:value={base} required hint={text.baseHint} />
		{#if menu.sellers.length > 1}
			<div class="flex flex-col gap-3">
				<p class="text-sm font-semibold text-slate-800">{text.perBranch}</p>
				<div class="grid gap-3 tablet:grid-cols-2">
					{#each menu.sellers as branch (branch.id)}
						<MoneyField label={branch.name} bind:value={own[branch.id]} hint={text.perBranchHint} />
					{/each}
				</div>
			</div>
		{/if}
	</div>

	{#if problem || menu.actionError}
		<div class="mt-4"><Banner tone="danger" icon="alert-triangle">{problem || menu.actionError}</Banner></div>
	{/if}

	{#snippet footer()}
		<Button label={actionText.cancel} disabled={menu.busy} onclick={() => menu.closeDialogs()} />
		<Button label={menu.busy ? actionText.saving : actionText.save} variant="primary" disabled={menu.busy} onclick={submit} />
	{/snippet}
</Modal>
