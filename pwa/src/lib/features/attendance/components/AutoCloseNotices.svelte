<script lang="ts">
	import DividedItems from '$lib/components/card/DividedItems.svelte';
	import ListCard from '$lib/components/card/ListCard.svelte';
	import ListRow from '$lib/components/card/ListRow.svelte';
	import PrimaryButton from '$lib/components/button/PrimaryButton.svelte';
	import { whenLabel } from '$lib/format/labels';
	import { t } from '$lib/text/t';
	import type { AutoCloseNotice } from '../models';

	/** Daftar absen yang ditutup otomatis oleh sistem, dengan tombol untuk menandainya sudah dibaca. */
	let { notices, acknowledging, onAcknowledge }: { notices: readonly AutoCloseNotice[]; acknowledging: boolean; onAcknowledge: () => void } = $props();
</script>

<div class="flex w-full flex-col gap-2">
	<ListCard>
		<DividedItems items={notices}>
			{#snippet row(notice)}
				<ListRow
					title={t('attendance_notice_title', notice.clockIn ? whenLabel(notice.clockIn) : '')}
					caption={notice.clockOut ? t('attendance_notice_caption', whenLabel(notice.clockOut)) : null}
				/>
			{/snippet}
		</DividedItems>
	</ListCard>
	<PrimaryButton text={t('attendance_notice_ack')} onclick={onAcknowledge} loading={acknowledging} />
</div>
