<script lang="ts">
	import { BLOCKED_LOGO, BLOCKED_TEXT } from './blocked';
</script>

<!-- Cadangan untuk kerangka yang tersimpan di perangkat; isinya sama dengan halaman penolakan dari server. -->
<div class="fixed inset-0 z-[100] flex items-center justify-center bg-background p-6">
	<main class="flex w-full max-w-[360px] flex-col items-center gap-4 text-center">
		<img src={BLOCKED_LOGO} alt="" class="w-36" />
		<h1 class="text-headline text-content">{BLOCKED_TEXT.title}</h1>
		<p class="text-body text-content-muted">{BLOCKED_TEXT.body}</p>
	</main>
</div>
