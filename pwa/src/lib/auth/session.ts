import { browser } from '$app/environment';
import type { UserOut } from '$lib/api/types';
import type { Permission } from './permissions';

const KEY = 'employee.session';
const MILLIS_PER_SECOND = 1000;

/** The signed-in user member as the server describes them; [permissions] only hide menus and are never the security check. */
export type UserProfile = {
	id: string;
	name: string | null;
	username: string;
	roleId: string | null;
	roleName: string;
	permissions: string[];
	/** Null means every branch (owner). */
	outletId: string | null;
	isActive: boolean;
	photoUrl: string | null;
	/** A property of the role sent by the server; a full-access role comes with empty [permissions]. */
	hasFullAccess: boolean;
};

/** The token is not kept in the page: the server puts it in a cookie scripts cannot read, so the page only knows who signed in. */
export type LoginSession = { user: UserProfile };

type Stored = { session: LoginSession; savedAtMillis: number; expiresInSeconds: number };

export const displayName = (user: UserProfile): string => user.name?.trim() || user.username;

export function profileOf(user: UserOut): UserProfile {
	return {
		id: user.id,
		name: user.name,
		username: user.username,
		roleId: user.role_id,
		roleName: user.role_name,
		permissions: user.permissions,
		outletId: user.outlet_id,
		isActive: user.is_active,
		photoUrl: user.photo_url,
		hasFullAccess: user.full_access
	};
}

/** Full-access roles may do everything and other roles only what is ticked; display only, the server still decides. */
export function can(user: UserProfile, permission: Permission): boolean {
	return user.hasFullAccess || user.permissions.includes(permission);
}

function isCurrentShape(value: unknown): value is Stored {
	const stored = value as Partial<Stored> | null;
	return typeof stored?.expiresInSeconds === 'number' && typeof stored.savedAtMillis === 'number' && typeof stored.session?.user?.hasFullAccess === 'boolean';
}

/** Null when this device holds no usable copy: never signed in, expired, unreadable, storage blocked, or saved by an earlier release. */
export function loadSession(): LoginSession | null {
	if (!browser) return null;
	try {
		const raw = localStorage.getItem(KEY);
		if (!raw) return null;
		const stored: unknown = JSON.parse(raw);
		// Earlier releases kept a token here or lacked the full-access mark; the copy is dropped and the cookie restores the account.
		if (!isCurrentShape(stored) || Date.now() - stored.savedAtMillis > stored.expiresInSeconds * MILLIS_PER_SECOND) {
			localStorage.removeItem(KEY);
			return null;
		}
		return stored.session;
	} catch {
		return null;
	}
}

/** A copy that lets the PWA open without the network; a device that refuses storage is restored from the cookie instead. */
export function saveSession(session: LoginSession, expiresInSeconds: number): void {
	if (!browser) return;
	try {
		localStorage.setItem(KEY, JSON.stringify({ session, savedAtMillis: Date.now(), expiresInSeconds } satisfies Stored));
	} catch {
		// Storage refused (private browsing or full): the cookie still signs this browser in at the next open.
	}
}

export function clearSession(): void {
	if (!browser) return;
	try {
		localStorage.removeItem(KEY);
	} catch {
		// Storage refused: there is no copy to remove.
	}
}
