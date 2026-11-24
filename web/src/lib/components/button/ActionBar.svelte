<script lang="ts">
	import { Menu, Portal } from '@skeletonlabs/skeleton-svelte';
	import Button from './Button.svelte';
	import MenuButton from './MenuButton.svelte';
	import type { Action } from './types';
	import { controlText } from '$lib/text/controls';

	let {
		primary,
		secondary = [],
		more = []
	}: {
		primary?: Action;
		secondary?: Action[];
		more?: Action[];
	} = $props();
</script>

<div class="flex flex-nowrap items-center gap-2">
	{#each secondary as action (action.label)}
		{#if action.items}
			<MenuButton label={action.label} icon={action.icon} items={action.items} disabled={action.disabled} hint={action.hint} compact />
		{:else}
			<Button
				label={action.label}
				icon={action.icon}
				variant={action.danger ? 'danger' : 'secondary'}
				active={action.active}
				disabled={action.disabled}
				hint={action.hint}
				onclick={action.onclick}
				compact
			/>
		{/if}
	{/each}

	{#if primary}
		<Button
			label={primary.label}
			icon={primary.icon}
			variant="primary"
			disabled={primary.disabled}
			hint={primary.hint}
			onclick={primary.onclick}
		/>
	{/if}

	{#if more.length > 0}
		<Menu onSelect={(details) => more.find((action) => action.label === details.value)?.onclick()}>
			<Menu.Trigger class="btn-icon btn-icon-sm border border-slate-200 bg-white text-slate-600 hover:border-brand-line hover:bg-brand-soft hover:text-brand hover:brightness-100" aria-label={controlText.moreActions}>
				<i class="ti ti-dots-vertical text-xl" aria-hidden="true"></i>
			</Menu.Trigger>
			<Portal>
				<Menu.Positioner>
					<Menu.Content class="z-40 w-56 rounded-lg border border-slate-200 bg-white p-1 shadow-xl outline-none">
						{#each more as action (action.label)}
							<Menu.Item
								value={action.label}
								disabled={action.disabled}
								class="flex cursor-pointer items-center gap-2 rounded-md px-3 py-2 text-sm font-medium data-highlighted:bg-brand-soft data-disabled:opacity-50 {action.danger ? 'text-danger-700' : 'text-slate-700'}"
							>
								<i class="ti ti-{action.icon} text-base" aria-hidden="true"></i>
								{action.label}
							</Menu.Item>
						{/each}
					</Menu.Content>
				</Menu.Positioner>
			</Portal>
		</Menu>
	{/if}
</div>
