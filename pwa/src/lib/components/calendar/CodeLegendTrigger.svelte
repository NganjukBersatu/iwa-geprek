<script lang="ts">
	import CodeBadge from '$lib/components/card/CodeBadge.svelte';
	import DividedItems from '$lib/components/card/DividedItems.svelte';
	import ListCard from '$lib/components/card/ListCard.svelte';
	import ListRow from '$lib/components/card/ListRow.svelte';
	import AppIcon from '$lib/components/icon/AppIcon.svelte';
	import BottomSheet from '$lib/components/sheet/BottomSheet.svelte';
	import type { CodeLegendItem } from './types';

	/** Baris ikon dan judul yang membuka lembar berisi daftar arti tiap kode, supaya daftarnya tidak memenuhi halaman. */
	let { title, items }: { title: string; items: readonly CodeLegendItem[] } = $props();

	let open = $state(false);
</script>

<button type="button" onclick={() => (open = true)} class="flex w-full items-center gap-2 px-2 py-2">
	<AppIcon icon="Info" tint="primary" />
	<span class="text-label text-primary">{title}</span>
</button>

{#if open}
	<BottomSheet {title} onDismiss={() => (open = false)}>
		<div class="pb-4">
			<ListCard>
				<DividedItems {items}>
					{#snippet row(item)}
						<ListRow title={item.title} detail={item.detail} caption={item.caption}>
							{#snippet trailing()}<CodeBadge text={item.code} color={item.color} />{/snippet}
						</ListRow>
					{/snippet}
				</DividedItems>
			</ListCard>
		</div>
	</BottomSheet>
{/if}
