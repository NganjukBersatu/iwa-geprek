<script lang="ts">
	import DividedItems from '$lib/components/card/DividedItems.svelte';
	import ListCard from '$lib/components/card/ListCard.svelte';
	import ListRow from '$lib/components/card/ListRow.svelte';
	import PrimaryButton from '$lib/components/button/PrimaryButton.svelte';
	import IconBadge from '$lib/components/icon/IconBadge.svelte';
	import BottomSheet from './BottomSheet.svelte';
	import type { NoticeSheetItem } from './types';

	/** Pengumuman yang tidak mengunci apa pun: ditutup lewat tombol, ketuk di luar, atau Esc. */
	let { title, items, closeLabel, onClose }: { title: string; items: readonly NoticeSheetItem[]; closeLabel: string; onClose: () => void } = $props();
</script>

<BottomSheet {title} onDismiss={onClose}>
	<div class="flex w-full flex-col gap-3">
		<ListCard>
			<DividedItems {items}>
				{#snippet row(item)}
					<ListRow title={item.title} caption={item.caption}>
						{#snippet leading()}{#if item.icon}<IconBadge icon={item.icon} />{/if}{/snippet}
					</ListRow>
				{/snippet}
			</DividedItems>
		</ListCard>
		<PrimaryButton text={closeLabel} onclick={onClose} />
	</div>
</BottomSheet>
