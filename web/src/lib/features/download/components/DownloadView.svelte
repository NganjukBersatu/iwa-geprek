<script lang="ts">
	import Button from '$lib/components/button/Button.svelte';
	import Tabs from '$lib/components/tabs/Tabs.svelte';
	import { enter } from '$lib/motion/transitions';
	import { motionReduced } from '$lib/motion/reduced';
	import { androidFile, type AndroidFile, ANDROID_MINIMUM, APK_NAME, APK_URL, IOS_RELEASE, IOS_RELEASE_NOTES, IOS_WEB_URL, RELEASE, RELEASE_NOTES } from '../release';
	import { ANDROID_STEPS, ATTENDANCE_GUIDE, IOS_STEPS, TABLET_GUIDE } from '$lib/text/download-guide';
	import { downloadText as t } from '$lib/text/download';
	import { format } from '$lib/text/format';
	import logo from '$lib/assets/logo/brand-logo.png';
	import PlatformCard from './PlatformCard.svelte';
	import GuideView from './GuideView.svelte';
	// Sapaan pembuka dimatikan untuk klien ini atas permintaan Safjar; buka komentar ini dan baris WelcomeIntro di bawah untuk menyalakannya lagi.
	// import WelcomeIntro from './WelcomeIntro.svelte';

	const LOGO = logo;
	const TABS = [
		{ key: 'android', icon: 'brand-android', label: t.tabAndroid },
		{ key: 'iphone', icon: 'brand-apple', label: t.tabIphone },
		{ key: 'tablet', icon: 'device-tablet', label: t.tabTablet },
		{ key: 'attendance', icon: 'fingerprint', label: t.tabAttendance }
	];

	let tab = $state('android');
	let tabBar = $state<HTMLElement | null>(null);
	let playing = $state(false);
	let copied = $state(false);
	let copyFailed = $state(false);
	let apk = $state<AndroidFile | null>(null);

	// Gagal bertanya berarti tombol unduh tidak ditawarkan, sama seperti saat berkasnya belum ada.
	androidFile().then((found) => (apk = found), () => (apk = null));

	// A tab picked after scrolling down brings the row of tabs back into view.
	function pick(key: string): void {
		tab = key;
		if (tabBar && tabBar.getBoundingClientRect().top < 0) tabBar.scrollIntoView({ behavior: motionReduced() ? 'auto' : 'smooth' });
	}

	async function copyAddress(): Promise<void> {
		if (!IOS_WEB_URL) return;
		try {
			await navigator.clipboard.writeText(IOS_WEB_URL);
			copied = true;
			setTimeout(() => (copied = false), 1800);
		} catch {
			// The address is shown for copying by hand only when the clipboard is refused.
			copyFailed = true;
		}
	}
</script>

<svelte:head><title>{t.pageTitle}</title></svelte:head>

<!-- <WelcomeIntro bind:playing logo={LOGO} /> -->

<div class="min-h-dvh bg-brand-page text-slate-800" class:welcome-pending={playing}>
	<header class="mx-auto flex max-w-6xl items-center gap-3 px-4 py-5 tablet:px-6">
		<div class="welcome-rise flex items-center gap-3">
			<img src={LOGO} alt={t.logoAlt} class="size-11 rounded-xl object-cover" />
			<div>
				<p class="font-bold leading-tight">
					{t.appName}
					<span class="ml-1 rounded-md bg-brand-accent px-1.5 py-0.5 align-middle text-[0.68rem] font-bold uppercase tracking-wide text-brand-deep">{RELEASE.version}</span>
				</p>
				<p class="text-xs text-slate-500">{t.downloadPage}</p>
			</div>
		</div>
	</header>

	<main class="mx-auto flex max-w-6xl flex-col px-4 tablet:px-6">
		<section class="flex flex-col py-6 tablet:py-10">
			<h1 class="welcome-rise text-4xl font-extrabold leading-tight tracking-tight text-brand-deep tablet:text-6xl">{t.heading} <span class="headline-mark">{t.brand}</span></h1>
			<p class="welcome-rise mt-4 text-slate-600 tablet:text-lg">{t.audience}</p>
			<div bind:this={tabBar} class="welcome-rise mt-6 scroll-mt-4">
				<Tabs tabs={TABS} bind:value={() => tab, pick} label={t.pickDevice} variant="pill" />
			</div>
		</section>

		{#if tab === 'android'}
			<div class="pb-10" in:enter={{ y: 16 }}>
				<PlatformCard tone="brand" steps={ANDROID_STEPS} screens={[androidDownload, androidAllow, androidInstall, androidOpen]} note={{ icon: 'shield-check', text: t.androidNote }}>
					<div class="flex items-center gap-3">
						<span class="flex size-12 items-center justify-center rounded-2xl bg-white/15 text-2xl text-brand-accent"><i class="ti ti-brand-android" aria-hidden="true"></i></span>
						<p class="text-xs font-bold uppercase tracking-widest text-brand-accent">{t.androidKicker}</p>
					</div>
					<h2 class="mt-4 text-3xl font-bold tracking-tight tablet:text-4xl">{t.androidTitle}</h2>
					<p class="mt-3 text-white/80">{t.androidSubtitle}</p>
					<p class="mt-4 flex flex-wrap gap-x-5 gap-y-1.5 text-sm text-white/80">
						<span class="inline-flex items-center gap-1.5"><i class="ti ti-apps" aria-hidden="true"></i>{t.version} <b class="font-mono text-white">{RELEASE.version}</b></span>
						{#if apk}
							<span class="inline-flex items-center gap-1.5"><i class="ti ti-download" aria-hidden="true"></i>{format(t.sizeMb, { size: apk.sizeMb })}</span>
						{/if}
						<span class="inline-flex items-center gap-1.5"><i class="ti ti-device-mobile" aria-hidden="true"></i>{format(t.orNewer, { version: ANDROID_MINIMUM })}</span>
					</p>
					{#if RELEASE_NOTES.length > 0}
						<div class="mt-5 rounded-2xl bg-white/10 p-4">
							<p class="text-xs font-bold uppercase tracking-widest text-brand-accent">{format(t.updateOfVersion, { version: RELEASE.version })}</p>
							<ul class="mt-3 grid gap-2 text-sm text-white/90">
								{#each RELEASE_NOTES as note (note.text)}
									<li class="flex items-center gap-2"><i class="ti ti-{note.icon} text-brand-accent" aria-hidden="true"></i>{note.text}</li>
								{/each}
							</ul>
						</div>
					{/if}
					{#if apk}
						<a href={APK_URL} download={APK_NAME} class="mt-6 inline-flex w-full items-center justify-center gap-2 self-start rounded-full bg-brand-accent px-7 py-4 font-bold text-brand-deep transition hover:-translate-y-0.5 hover:bg-brand-accent-deep motion-reduce:transition-none tablet:w-auto">
							<i class="ti ti-download text-lg" aria-hidden="true"></i>{t.downloadApk}
						</a>
					{:else}
						<span class="mt-6 inline-flex w-full items-center justify-center gap-2 self-start rounded-full bg-white/15 px-7 py-4 font-bold text-white/80 tablet:w-auto" aria-disabled="true">
							<i class="ti ti-clock text-lg" aria-hidden="true"></i>{t.apkSoon}
						</span>
					{/if}
				</PlatformCard>
			</div>
		{:else if tab === 'iphone'}
			<div class="pb-10" in:enter={{ y: 16 }}>
				<PlatformCard tone="light" steps={IOS_STEPS} screens={[iosSafari, iosShare, iosAdd, iosHome]} note={{ icon: 'brand-android', text: t.iosNote }}>
					<div class="flex items-center gap-3">
						<span class="flex size-12 items-center justify-center rounded-2xl bg-brand-tint text-2xl text-brand-deep"><i class="ti ti-brand-apple" aria-hidden="true"></i></span>
						<p class="text-xs font-bold uppercase tracking-widest text-brand">{t.tabIphone}</p>
					</div>
					<h2 class="mt-4 text-3xl font-bold tracking-tight text-brand-deep tablet:text-4xl">{t.iosTitle}</h2>
					<p class="mt-3 text-slate-600">{t.iosSubtitle}</p>
					<p class="mt-4 flex flex-wrap gap-x-5 gap-y-1.5 text-sm text-slate-500">
						<span class="inline-flex items-center gap-1.5"><i class="ti ti-apps" aria-hidden="true"></i>{t.version} <b class="font-mono text-slate-800">{IOS_RELEASE.version}</b></span>
						<span class="inline-flex items-center gap-1.5"><i class="ti ti-brand-safari" aria-hidden="true"></i>{t.safariOnIos}</span>
					</p>
					{#if IOS_RELEASE_NOTES.length > 0}
						<div class="mt-5 rounded-2xl bg-brand-page p-4">
							<p class="text-xs font-bold uppercase tracking-widest text-brand">{format(t.updateOfVersion, { version: IOS_RELEASE.version })}</p>
							<ul class="mt-3 grid gap-2 text-sm text-slate-700">
								{#each IOS_RELEASE_NOTES as note (note.text)}
									<li class="flex items-center gap-2"><i class="ti ti-{note.icon} text-brand" aria-hidden="true"></i>{note.text}</li>
								{/each}
							</ul>
						</div>
					{/if}
					{#if IOS_WEB_URL}
						<p class="mt-5 flex flex-wrap items-center gap-2">
							<Button label={copied ? t.copied : t.copyAddress} icon={copied ? 'check' : 'copy'} onclick={() => void copyAddress()} />
							{#if copyFailed}
								<code class="select-all rounded-xl border border-dashed border-brand-line bg-brand-page px-3 py-2 font-mono text-sm wrap-anywhere">{IOS_WEB_URL}</code>
							{/if}
						</p>
					{:else}
						<p class="mt-5 inline-flex items-center gap-2 self-start rounded-xl bg-brand-tint px-3 py-2 text-sm font-semibold text-brand-deep"><i class="ti ti-clock" aria-hidden="true"></i>{t.webAddressSoon}</p>
					{/if}
				</PlatformCard>
			</div>
		{/if}
	</main>

	{#if tab === 'tablet'}
		<div in:enter={{ y: 16 }}>
			<GuideView guide={TABLET_GUIDE} />
		</div>
	{:else if tab === 'attendance'}
		<div in:enter={{ y: 16 }}>
			<GuideView guide={ATTENDANCE_GUIDE} />
		</div>
	{/if}

	<footer class="border-t border-white/15 bg-brand-deep px-4 py-6 text-sm text-white/80 tablet:px-6">
		<div class="mx-auto max-w-6xl">{t.footer}</div>
	</footer>
</div>

{#snippet androidDownload()}
	<span class="phone-icon"><i class="ti ti-download" aria-hidden="true"></i></span>
	<p class="phone-title">{APK_NAME}</p>
	<p class="phone-text">{t.phoneDownloading}</p>
	<span class="phone-bar"><i></i></span>
{/snippet}

{#snippet androidAllow()}
	<p class="phone-title">{t.phoneUnknownApps}</p>
	<p class="phone-text">{t.phoneBrowser}</p>
	<span class="phone-toggle">{t.phoneAllowSource}<i></i></span>
{/snippet}

{#snippet androidInstall()}
	<img src={LOGO} alt="" class="phone-icon" />
	<p class="phone-title">{t.appName}</p>
	<p class="phone-text">{t.phoneInstallQuestion}</p>
	<span class="flex gap-2"><span class="phone-ghost">{t.phoneCancel}</span><span class="phone-pill">{t.phoneInstall}</span></span>
{/snippet}

{#snippet androidOpen()}
	<img src={LOGO} alt="" class="phone-icon" />
	<p class="phone-title">{t.phoneInstalled}</p>
	<span class="flex gap-2"><span class="phone-ghost">{t.phoneDone}</span><span class="phone-pill">{t.phoneOpen}</span></span>
{/snippet}

{#snippet iosSafari()}
	<span class="phone-icon"><i class="ti ti-brand-safari" aria-hidden="true"></i></span>
	<p class="phone-title">{t.safari}</p>
	<p class="phone-text">{t.phoneOpeningWeb}</p>
	<span class="phone-bar"><i></i></span>
{/snippet}

{#snippet iosShare()}
	<p class="phone-title">{t.phoneSafariBar}</p>
	<p class="phone-text">{t.phoneTapShare}</p>
	<span class="phone-pill"><i class="ti ti-share-2" aria-hidden="true"></i></span>
{/snippet}

{#snippet iosAdd()}
	<span class="phone-sheet">
		<span>{t.phoneCopy}</span>
		<span class="phone-sheet-hit">{t.phoneAddToHome} <i class="ti ti-square-plus" aria-hidden="true"></i></span>
		<span>{t.phoneAddFavorite}</span>
	</span>
{/snippet}

{#snippet iosHome()}
	<span class="phone-home">
		{#each { length: 8 } as _, cell (cell)}
			{#if cell === 5}<img src={LOGO} alt="" class="phone-home-app" />{:else}<span></span>{/if}
		{/each}
	</span>
	<p class="phone-text">{t.phoneOnHome}</p>
{/snippet}
