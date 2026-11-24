<script lang="ts">
	import { afterNavigate, beforeNavigate, goto, replaceState } from '$app/navigation';
	import { page } from '$app/state';
	import { onMount } from 'svelte';
	import { api } from '$lib/api';
	import ConfirmDialog from '$lib/components/dialog/ConfirmDialog.svelte';
	import UnsavedChangesDialog from '$lib/components/dialog/UnsavedChangesDialog.svelte';
	import { authText } from '$lib/text/auth';
	import { unsavedChanges } from '$lib/components/form/unsaved-changes.svelte';
	import ToastView from '$lib/components/feedback/ToastView.svelte';
	import WhatsNewDialog from '$lib/features/release/components/WhatsNewDialog.svelte';
	import ScreenGate from '$lib/components/gate/ScreenGate.svelte';
	import ConnectionBar from '$lib/components/motion/ConnectionBar.svelte';
	import NavProgress from '$lib/components/motion/NavProgress.svelte';
	import MobileHeader from '$lib/components/header/MobileHeader.svelte';
	import Sidebar from '$lib/components/sidebar/Sidebar.svelte';
	import { clearSession, getUser, isSignedIn, mayEnterWeb, saveUser, USER_CHANGED_EVENT } from '$lib/auth/session';
	import { endSignIn, SIGN_OUT_FAILED } from '$lib/auth/sign-out';
	import { toast } from '$lib/components/feedback/toast.svelte';
	import { applyFilters, hasFilters, withoutFilters } from '$lib/nav/link-filters';
	import { SIGN_IN_PATH } from '$lib/nav/pages';
	import { signInPathFor } from '$lib/nav/return-to';
	import { webBrand, webNav, webProfile } from '$lib/nav/webNav';
	import { enterScreen } from '$lib/components/pager/page-memory';
	import { pageSize } from '$lib/components/pager/size.svelte';
	import { restoreBranch } from '$lib/stores/branch';
	import { scrollShadow } from '$lib/motion/actions';
	import { pageTransition } from '$lib/motion/page-transition';
	import { navProgress } from '$lib/motion/progress.svelte';
	import { spotlight } from '$lib/motion/spotlight';

	let { children } = $props();

	// What the account chose last time (its branch and rows per page) is in place before any page asks for it.
	restoreBranch();
	pageSize.restore();

	// Saringan yang dibawa tautan berlaku sebelum halaman tujuan memuat datanya.
	if (hasFilters(page.url)) applyFilters(page.url);

	pageTransition();
	let stopSpotlight = () => {};
	// What waits for the answer to "leave without saving?"; null means nobody is asking.
	let pendingLeave = $state<(() => void) | null>(null);

	function discardAndLeave(): void {
		const proceed = pendingLeave;
		pendingLeave = null;
		unsavedChanges.clear();
		proceed?.();
	}

	beforeNavigate((navigation) => {
		if (unsavedChanges.has) {
			// Closing the tab or opening another site gets the browser's own question; moving inside the app gets ours.
			navigation.cancel();
			const target = navigation.to?.url;
			if (!navigation.willUnload && target) pendingLeave = () => void goto(target);
			return;
		}
		if (navigation.to?.url.pathname !== navigation.from?.url.pathname) navProgress.start();
		if (navigation.to && hasFilters(navigation.to.url)) applyFilters(navigation.to.url);
	});
	afterNavigate((navigation) => {
		if (navigation.to && hasFilters(navigation.to.url)) replaceState(withoutFilters(navigation.to.url), page.state);
		navProgress.arrived();
		stopSpotlight();
		stopSpotlight = spotlight(navigation.to?.url.hash ?? '');
	});

	let ready = $state(false);
	let user = $state(getUser());
	let collapsed = $state(false);
	let mobileOpen = $state(false);

	const profile = $derived({ ...webProfile, subtitle: user?.username, photoUrl: user?.photo_url });

	// The server revokes this sign-in and clears its cookie; the page forgets the account whether or not that call gets through.
	function signOut(): void {
		void api.auth
			.logout()
			.catch(() => {})
			.finally(() => {
				// An ended sign-in cannot be saved into, so nothing is asked.
				unsavedChanges.clear();
				clearSession();
				void goto(signInPathFor(page.url.pathname + page.url.search), { replaceState: true });
			});
	}

	// Signing out always asks first; the question also says so when a form holds changes that would be lost.
	let confirmingSignOut = $state(false);

	function requestLeave(): void {
		confirmingSignOut = true;
	}

	function confirmSignOut(): void {
		confirmingSignOut = false;
		unsavedChanges.clear();
		void leave();
	}

	async function leave(): Promise<void> {
		if (await endSignIn()) void goto(SIGN_IN_PATH, { replaceState: true });
		else toast.show(SIGN_OUT_FAILED, 'error');
	}

	onMount(() => {
		if (!isSignedIn() || !mayEnterWeb(getUser())) {
			signOut();
			return;
		}
		ready = true;
		api.auth
			.me()
			.then((latest) => {
				if (!mayEnterWeb(latest)) return signOut();
				saveUser(latest);
				user = latest;
			})
			.catch(() => {});
	});

	$effect(() => {
		void page.url.pathname;
		enterScreen();
	});

	// The profile page changes the name and photo; the sidebar follows.
	$effect(() => {
		const reread = () => (user = getUser());
		window.addEventListener(USER_CHANGED_EVENT, reread);
		return () => window.removeEventListener(USER_CHANGED_EVENT, reread);
	});
</script>

{#if ready}
	<div class="flex h-screen supports-[height:100dvh]:h-dvh flex-col overflow-hidden bg-brand-soft text-slate-800 tablet:flex-row">
		<Sidebar
			entries={webNav}
			brand={webBrand}
			{profile}
			path={page.url.pathname}
			onsignout={requestLeave}
			bind:collapsed
			bind:mobileOpen
		/>
		<MobileHeader brand={webBrand} bind:menuOpen={mobileOpen} />

		<main class="flex min-w-0 flex-1 flex-col overflow-hidden">
			<ConnectionBar />
			<!-- relative keeps absolutely placed content, such as sr-only labels, inside this scroll area instead of stretching the document. -->
			<div use:scrollShadow={'[data-mobile-header]'} class="relative flex-1 overflow-y-auto p-3 hp-besar:p-4 tablet:p-6 laptop:p-8" data-page-scroll>
				<div class="page-transition mx-auto w-full max-w-(--page-max)">
					<ScreenGate>{@render children()}</ScreenGate>
				</div>
			</div>
		</main>
	</div>
	<ToastView />
	<ConfirmDialog open={confirmingSignOut} title={authText.signOutTitle} confirmLabel={authText.signOutConfirm} onconfirm={confirmSignOut} oncancel={() => (confirmingSignOut = false)}>
		{unsavedChanges.has ? authText.signOutUnsavedBody : authText.signOutBody}
	</ConfirmDialog>
	<UnsavedChangesDialog open={pendingLeave !== null} ondiscard={discardAndLeave} onstay={() => (pendingLeave = null)} />
	<WhatsNewDialog />
{/if}
<NavProgress />
