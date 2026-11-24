<script lang="ts">
	import type { SopMedia } from '$lib/api/types';
	import RichEditor from '$lib/components/editor/RichEditor.svelte';
	import TextField from '$lib/components/form/TextField.svelte';
	import type { SlideDraft } from '../sop-draft.svelte';
	import { sopText } from '$lib/text/sop';

	let { slide, onupload }: { slide: SlideDraft; onupload: (file: File) => Promise<SopMedia> } = $props();
</script>

<div class="flex flex-col gap-4 p-4 tablet:p-5">
	<TextField label={sopText.slideTitle} bind:value={slide.title} maxlength={120} required placeholder={sopText.slideTitleExample} />
	<RichEditor label={sopText.slideBody} bind:value={slide.body} placeholder={sopText.slideBodyHint} {onupload} />
</div>
