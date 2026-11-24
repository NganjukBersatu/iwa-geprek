<script lang="ts">
	import { untrack } from 'svelte';
	import PrimaryButton from '$lib/components/button/PrimaryButton.svelte';
	import ChoiceFlow from '$lib/components/choice/ChoiceFlow.svelte';
	import TextField from '$lib/components/field/TextField.svelte';
	import InlineMessage from '$lib/components/feedback/InlineMessage.svelte';
	import AttachmentGallery from '$lib/components/media/AttachmentGallery.svelte';
	import PhotoField from '$lib/components/media/PhotoField.svelte';
	import BottomSheet from '$lib/components/sheet/BottomSheet.svelte';
	import AppText from '$lib/components/text/AppText.svelte';
	import type { PickedPhoto } from '$lib/platform/photo';
	import { t } from '$lib/text/t';
	import { TOGGLE_OK, TOGGLE_PROBLEM, type Batch, type BatchAnswer, type BatchItem } from '../batches';

	/** Lembar isi tugas outlet. Seluruh item diisi sekaligus lalu diselesaikan; item wajib yang kosong menahan penyelesaian dengan keterangan item mana yang kurang, sedangkan item opsional boleh dikosongkan. */
	let {
		batch,
		submitting,
		error,
		onSubmit,
		onDismiss,
		initialValues = {},
		keptPhotoUrls = {},
		submitLabel = t('batch_submit')
	}: {
		batch: Batch;
		submitting: boolean;
		error: string | null;
		onSubmit: (answers: BatchAnswer[]) => void;
		onDismiss: () => void;
		/** Jawaban dan foto yang sudah tersimpan saat form dipakai untuk memperbaiki pengisian. */
		initialValues?: Record<string, string>;
		keptPhotoUrls?: Record<string, string>;
		submitLabel?: string;
	} = $props();

	let values = $state<Record<string, string>>(Object.fromEntries(untrack(() => batch.items).map((item) => [item.id, untrack(() => initialValues)[item.id] ?? ''])));
	let photos = $state<Record<string, PickedPhoto>>({});
	let localError = $state<string | null>(null);

	const isEmpty = (item: BatchItem): boolean => (item.kind === 'photo' ? !photos[item.id] && !keptPhotoUrls[item.id] : !(values[item.id] ?? '').trim());
	const labelOf = (item: BatchItem): string => item.label + (item.required ? '' : t('batch_optional_suffix'));

	function submit(): void {
		const missing = batch.items.filter((item) => item.required && isEmpty(item));
		if (missing.length > 0) {
			localError = t('batch_missing', missing.map((item) => item.label).join(', '));
			return;
		}
		onSubmit(
			batch.items.flatMap((item): BatchAnswer[] => {
				if (isEmpty(item)) return [];
				// Foto tersimpan tetap dipakai selama belum diganti foto baru.
				if (item.kind === 'photo') return [{ itemId: item.id, value: null, photo: photos[item.id]?.blob ?? null, keepPhoto: !photos[item.id] }];
				return [{ itemId: item.id, value: (values[item.id] ?? '').trim(), photo: null }];
			})
		);
	}
</script>

<BottomSheet title={batch.name} {onDismiss}>
	<div class="flex w-full flex-col gap-3">
		{#each batch.items as item (item.id)}
			{#if item.kind === 'text' || item.kind === 'number'}
				<TextField
					label={labelOf(item)}
					enabled={!submitting}
					inputmode={item.kind === 'number' ? 'decimal' : undefined}
					oninput={() => (localError = null)}
					bind:value={values[item.id]}
				/>
			{:else if item.kind === 'toggle'}
				<ChoiceFlow
					label={labelOf(item)}
					options={[t('batch_toggle_ok'), t('batch_toggle_problem')]}
					selectedIndex={values[item.id] === TOGGLE_OK ? 0 : values[item.id] === TOGGLE_PROBLEM ? 1 : null}
					onselect={(index) => {
						values[item.id] = index === 0 ? TOGGLE_OK : TOGGLE_PROBLEM;
						localError = null;
					}}
				/>
			{:else}
				<div class="flex flex-col gap-1">
					<AppText role="label">{labelOf(item)}</AppText>
					{#if !photos[item.id] && keptPhotoUrls[item.id]}
						<AttachmentGallery attachments={[{ id: item.id, isVideo: false, url: keptPhotoUrls[item.id] ?? '', removable: false }]} />
					{/if}
					<PhotoField
						photo={photos[item.id] ?? null}
						onPicked={(picked) => {
							photos[item.id] = picked;
							localError = null;
						}}
						enabled={!submitting}
					/>
				</div>
			{/if}
		{/each}
		{#if error ?? localError}<InlineMessage text={error ?? localError ?? ''} />{/if}
		<PrimaryButton text={submitLabel} onclick={submit} enabled={!submitting} loading={submitting} />
	</div>
</BottomSheet>
