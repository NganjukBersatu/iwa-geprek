<script lang="ts">
	import { dynamicStyle } from '$lib/platform/dynamic-style';
	import DividedItems from '$lib/components/card/DividedItems.svelte';
	import IconBadge from '$lib/components/card/IconBadge.svelte';
	import ListRow from '$lib/components/card/ListRow.svelte';
	import StateListCard from '$lib/components/card/StateListCard.svelte';
	import FailureState from '$lib/components/feedback/FailureState.svelte';
	import StatusBadge from '$lib/components/feedback/StatusBadge.svelte';
	import StoryPlayer from '$lib/components/story/StoryPlayer.svelte';
	import Notice from '$lib/components/feedback/Notice.svelte';
	import { t } from '$lib/text/t';
	import { SopState } from '../sop.svelte';

	let { onSessionExpired }: { onSessionExpired: () => void } = $props();

	const sop = new SopState(() => onSessionExpired());

	$effect(() => {
		void sop.load();
	});
</script>

{#if sop.opened}
	{@const opened = sop.opened}
	<StoryPlayer
		pages={opened.slides}
		title={opened.title}
		previousLabel={t('sop_previous')}
		nextLabel={t('sop_next')}
		finishLabel={t('sop_finish')}
		progressLabel={(currentPage, total) => `${currentPage}/${total}`}
		onFinish={() => sop.finish()}
	/>
{:else}
	<div class="flex size-full justify-center overflow-y-auto">
		<div class="flex w-full max-w-[var(--size-content-max)] flex-col gap-2" use:dynamicStyle={{ padding: '16px var(--page-padding)' }}>
			{#if sop.openFailure}<FailureState failure={sop.openFailure} />{/if}
			{#if sop.readFailure}
				<Notice text={t('sop_read_not_sent')} />
				<FailureState failure={sop.readFailure} onRetry={() => sop.retryRead()} />
			{/if}
			{#if sop.failure}
				<FailureState failure={sop.failure} onRetry={() => void sop.load()} />
			{:else}
				<StateListCard loading={sop.loading} empty={sop.items.length === 0} emptyText={t('sop_empty')}>
					<DividedItems items={sop.items}>
						{#snippet row(item)}
							<ListRow title={item.title} caption={t('sop_slide_count', String(item.slideCount))} onclick={() => void sop.open(item)}>
								{#snippet leading()}<IconBadge icon="Book" />{/snippet}
								{#snippet trailing()}
									{#if sop.isNew(item)}<StatusBadge text={t('sop_new')} tone="positive" />{/if}
								{/snippet}
							</ListRow>
						{/snippet}
					</DividedItems>
				</StateListCard>
			{/if}
		</div>
	</div>
{/if}
