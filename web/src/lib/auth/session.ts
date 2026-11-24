import { browser } from '$app/environment';
import type { User } from '$lib/api/types';

// Older builds kept the token here; it is removed on every save or sign-out.
const LEGACY_TOKEN_KEY = 'web.token';
const USER_KEY = 'web.user';

/** Decided by the server from the account's role, so no screen spells out the permission key. A session saved before the field
 * existed is let through only until the fresh account from /me answers; an explicit false always keeps the account out. */
export function mayEnterWeb(user: { web_access?: boolean } | null | undefined): boolean {
	return !!user && user.web_access !== false;
}

/** Only the account is kept in the page; the token stays in a cookie the page cannot read, set by the server at sign-in. */
export function saveSession(user: User): void {
	if (!browser) return;
	localStorage.removeItem(LEGACY_TOKEN_KEY);
	localStorage.setItem(USER_KEY, JSON.stringify(user));
}

export const USER_CHANGED_EVENT = 'web:user-changed';

/** Saves the signed-in user and tells the open page (the sidebar shows the name and photo) to read it again. */
export function saveUser(user: User): void {
	if (!browser) return;
	localStorage.setItem(USER_KEY, JSON.stringify(user));
	window.dispatchEvent(new CustomEvent(USER_CHANGED_EVENT));
}

export function getUser(): User | null {
	if (!browser) return null;
	const raw = localStorage.getItem(USER_KEY);
	if (!raw) return null;
	try {
		return JSON.parse(raw) as User;
	} catch {
		return null;
	}
}

export function clearSession(): void {
	if (!browser) return;
	localStorage.removeItem(LEGACY_TOKEN_KEY);
	localStorage.removeItem(USER_KEY);
}

export function isSignedIn(): boolean {
	return getUser() !== null;
}
