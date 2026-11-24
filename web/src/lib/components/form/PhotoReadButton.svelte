<script lang="ts">
	import { formText } from '$lib/text/form';
	import { preparePhoto, READING_MAX_SIDE } from '$lib/image/shrink';

	let {
		label,
		disabled = false,
		onread
	}: {
		label: string;
		disabled?: boolean;
		/** Gets the photo at reading resolution; the button stays busy until it resolves. */
		onread: (photo: File) => Promise<void>;
	} = $props();

	let reading = $state(false);

	async function pick(event: Event & { currentTarget: HTMLInputElement }): Promise<void> {
		const chosen = event.currentTarget.files?.[0];
		event.currentTarget.value = '';
		if (!chosen) return;
		reading = true;
		try {
			await onread(await preparePhoto(chosen, READING_MAX_SIDE));
		} finally {
			reading = false;
		}
	}
</script>

<label class="inline-flex w-fit cursor-pointer items-center gap-2 rounded-md bg-brand px-3 py-2 text-sm font-semibold text-white hover:bg-brand-hover {disabled || reading ? 'pointer-events-none opacity-60' : ''}">
	<i class="ti {reading ? 'ti-loader-2 animate-spin' : 'ti-scan'}" aria-hidden="true"></i>
	{reading ? formText.readingPhoto : label}
	<input type="file" accept="image/*" capture="environment" class="sr-only" disabled={disabled || reading} onchange={(event) => void pick(event)} />
</label>
