<script lang="ts">
	import { dynamicStyle } from '$lib/platform/dynamic-style';
	import jsQR from 'jsqr';
	import { onMount } from 'svelte';
	import Notice from '$lib/components/feedback/Notice.svelte';
	import { cameraProblemOf, cameraProblemText, type CameraProblem } from '$lib/platform/camera';

	/** Bingkai bidik sebagai bagian dari sisi pratinjau. */
	const FRAME_FRACTION = 0.7;
	const SCAN_INTERVAL_MILLIS = 120;
	const MAX_SCAN_SIDE_PX = 640;

	/** Pratinjau kamera belakang persegi dengan bingkai bidik; [onScanned] menerima isi QR yang terbaca (dipanggil berulang selama QR terlihat). */
	let { onScanned }: { onScanned: (value: string) => void } = $props();

	let video: HTMLVideoElement | undefined = $state();
	let problem = $state<CameraProblem | null>(null);

	onMount(() => {
		let stream: MediaStream | null = null;
		let timer: ReturnType<typeof setInterval> | undefined;
		let stopped = false;
		const canvas = document.createElement('canvas');
		const context = canvas.getContext('2d', { willReadFrequently: true });

		function scan(): void {
			if (!video || !context || video.readyState < video.HAVE_CURRENT_DATA || video.videoWidth === 0) return;
			const scale = Math.min(1, MAX_SCAN_SIDE_PX / Math.max(video.videoWidth, video.videoHeight));
			canvas.width = Math.round(video.videoWidth * scale);
			canvas.height = Math.round(video.videoHeight * scale);
			context.drawImage(video, 0, 0, canvas.width, canvas.height);
			const image = context.getImageData(0, 0, canvas.width, canvas.height);
			const code = jsQR(image.data, image.width, image.height, { inversionAttempts: 'dontInvert' });
			if (code?.data) onScanned(code.data);
		}

		void (async () => {
			try {
				stream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: { ideal: 'environment' } }, audio: false });
			} catch (error) {
				problem = cameraProblemOf(error);
				return;
			}
			if (stopped || !video) return stream.getTracks().forEach((track) => track.stop());
			video.srcObject = stream;
			await video.play().catch(() => undefined);
			timer = setInterval(scan, SCAN_INTERVAL_MILLIS);
		})();

		return () => {
			stopped = true;
			clearInterval(timer);
			stream?.getTracks().forEach((track) => track.stop());
		};
	});
</script>

<div class="relative aspect-square w-full overflow-hidden rounded-card bg-scrim">
	{#if problem}
		<div class="flex size-full items-center justify-center p-4"><Notice text={cameraProblemText(problem)} class="!text-on-primary" /></div>
	{:else}
		<video bind:this={video} playsinline muted autoplay class="size-full object-cover"></video>
		<div class="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 rounded-field border-2 border-accent" use:dynamicStyle={{ width: `${FRAME_FRACTION * 100}%`, height: `${FRAME_FRACTION * 100}%` }}></div>
	{/if}
</div>
