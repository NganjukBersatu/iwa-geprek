<script lang="ts">
	import type { Snippet } from 'svelte';
	import { dynamicStyle } from '$lib/motion/actions';
	import logo from '$lib/assets/logo/brand-logo.png';
	import storefront from '$lib/assets/photo/storefront.webp';
	import Button from '$lib/components/button/Button.svelte';
	import Banner from '$lib/components/card/Banner.svelte';
	import TextField from '$lib/components/form/TextField.svelte';
	import { authText } from '$lib/text/auth';
	import type { LoginField, LoginState } from '../login.svelte';

	// Sama dengan breakpoint laptop (64rem); di bawahnya hanya form yang tampil, tanpa foto toko.
	const WIDE_MIN_WIDTH = 1024;
	// Ukuran rancangan bingkai; di layar yang lebih kecil seluruh bingkai diperkecil sebanding supaya tidak perlu digulir.
	const DESIGN_WIDTH = 1200;
	const DESIGN_HEIGHT = 780;
	const FIT_MARGIN = 48;
	const MIN_FIT = 0.55;

	const text = authText.login;

	/** below: isi tambahan di bawah tombol Masuk yang disusun halaman, misalnya pintu masuk mode demo. */
	let { login, below }: { login: LoginState; below?: Snippet } = $props();

	let innerWidth = $state(0);
	let innerHeight = $state(0);
	const wide = $derived(innerWidth >= WIDE_MIN_WIDTH);
	const fit = $derived(
		Math.max(MIN_FIT, Math.min(1, (innerWidth - 2 * FIT_MARGIN) / DESIGN_WIDTH, (innerHeight - 2 * FIT_MARGIN) / DESIGN_HEIGHT))
	);
	let usernameField = $state<{ focus(): void }>();
	let passwordField = $state<{ focus(): void }>();
	const fieldFor = (field: LoginField) => (field === 'username' ? usernameField : passwordField);

	async function handleSubmit(event: SubmitEvent): Promise<void> {
		event.preventDefault();
		const invalid = login.validate();
		if (invalid) {
			fieldFor(invalid)?.focus();
			return;
		}
		await login.submit();
	}
</script>

<svelte:window bind:innerWidth bind:innerHeight />

<div class="flex min-h-dvh items-center justify-center bg-brand-page p-4 laptop:h-dvh laptop:overflow-hidden laptop:p-0">
	<!-- Bentuk tepi kanan foto: menyapu seperti huruf S dari atas ke bawah. -->
	<svg width="0" height="0" class="absolute" aria-hidden="true" focusable="false">
		<defs>
			<clipPath id="login-shape" clipPathUnits="objectBoundingBox">
				<path d="M0 0 L0.95 0 C1.00 0.14 0.85 0.26 0.80 0.40 C0.756 0.54 0.85 0.66 0.707 0.80 C0.634 0.88 0.56 0.94 0.512 1 L0 1 Z" />
			</clipPath>
		</defs>
	</svg>

	<main
		use:dynamicStyle={{ zoom: wide ? fit : undefined }}
		class="relative w-full max-w-md laptop:h-195 laptop:w-300 laptop:max-w-none laptop:shrink-0 laptop:overflow-hidden laptop:rounded-lg laptop:bg-white laptop:shadow-xl"
	>
		{#if wide}
			<div class="absolute inset-y-0 left-0 w-[82%] translate-x-4 bg-brand-tint [clip-path:url(#login-shape)]" aria-hidden="true"></div>
			<div class="absolute inset-y-0 left-0 w-[82%] overflow-hidden bg-brand-tint [clip-path:url(#login-shape)]">
				<img src={storefront} alt={text.imageAlt} width="1448" height="1086" class="size-full object-cover object-[30%_50%]" />
			</div>
		{/if}

		<form
			onsubmit={handleSubmit}
			novalidate
			class="relative flex w-full flex-col gap-5 rounded-lg border border-brand-line bg-white p-6 shadow-xl tablet:p-8 laptop:absolute laptop:top-[52%] laptop:right-12 laptop:w-md laptop:-translate-y-1/2 laptop:border-0 laptop:p-10"
		>
			<img src={logo} alt={text.logoAlt} width="88" height="116" class="h-auto w-22" />
			<h1 class="text-display font-semibold text-brand-ink">{text.heading}</h1>
			<div class="-mt-1 h-0.75 w-14 rounded-full bg-brand" aria-hidden="true"></div>

			<TextField bind:this={usernameField} label={text.username.label} autocomplete="username" placeholder={text.username.placeholder} required large error={login.usernameError} onblur={() => login.touch('username')} bind:value={login.username} />
			<TextField bind:this={passwordField} label={text.password.label} type="password" autocomplete="current-password" placeholder={text.password.placeholder} required large error={login.passwordError} onblur={() => login.touch('password')} bind:value={login.password} />

			<div aria-live="polite" class="empty:hidden">
				{#if login.message}
					<Banner tone="danger" icon="alert-triangle">{login.message}</Banner>
				{/if}
			</div>

			<Button type="submit" variant="primary" label={login.submitting ? text.submitting : text.submit} disabled={login.submitting} class="h-12! w-full justify-center rounded-full text-base!" />

			{@render below?.()}

			<p class="border-t border-brand-line pt-4 text-sm font-normal text-brand-muted laptop:whitespace-nowrap">{text.forgotPassword}</p>
		</form>
	</main>
</div>
