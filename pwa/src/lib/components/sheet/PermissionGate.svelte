<script lang="ts">
	import DividedItems from '$lib/components/card/DividedItems.svelte';
	import ListCard from '$lib/components/card/ListCard.svelte';
	import ListRow from '$lib/components/card/ListRow.svelte';
	import PrimaryButton from '$lib/components/button/PrimaryButton.svelte';
	import StatusBadge from '$lib/components/feedback/StatusBadge.svelte';
	import SuccessState from '$lib/components/feedback/SuccessState.svelte';
	import BottomSheet from './BottomSheet.svelte';
	import type { PermissionGateItem } from './types';

	/** Panel bawah yang tidak bisa ditutup pengguna; pemanggil menutupnya lewat [visible] false. */
	let {
		title,
		message,
		items,
		actionLabel,
		onAction,
		onClosed,
		visible = true,
		loading = false,
		footnote = '',
		completed = false,
		completedTitle = '',
		completedMessage = ''
	}: {
		title: string;
		message: string;
		items: readonly PermissionGateItem[];
		actionLabel: string;
		onAction: () => void;
		onClosed: () => void;
		visible?: boolean;
		loading?: boolean;
		footnote?: string;
		completed?: boolean;
		completedTitle?: string;
		completedMessage?: string;
	} = $props();
</script>

<BottomSheet {title} onDismiss={onClosed} dismissible={false} {visible}>
	{#if completed}
		<SuccessState title={completedTitle} message={completedMessage} icon="Checklist" />
	{:else}
		<p class="text-body m-0 text-content-muted">{message}</p>
		<div class="h-4"></div>
		<ListCard>
			<DividedItems {items}>
				{#snippet row(item)}
					<ListRow title={item.title} caption={item.description} onclick={item.onclick ?? undefined}>
						{#snippet trailing()}<StatusBadge text={item.statusText} tone={item.tone} />{/snippet}
					</ListRow>
				{/snippet}
			</DividedItems>
		</ListCard>
		<div class="h-4"></div>
		<PrimaryButton text={actionLabel} onclick={onAction} {loading} />
		{#if footnote}<p class="text-body m-0 mt-3 text-center text-content-muted">{footnote}</p>{/if}
	{/if}
</BottomSheet>
