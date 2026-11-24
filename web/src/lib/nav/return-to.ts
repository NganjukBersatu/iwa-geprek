import { SIGN_IN_PATH } from './pages';

const RETURN_PARAM = 'dari';
// Only pages of this app: a path from the address bar is never trusted as a destination otherwise.
const APP_ROOTS = ['/admin/', '/profile'];

/** The sign-in page that brings the person back to `current` (path and query) once they are in. */
export function signInPathFor(current: string): string {
	return safeReturnPath(current) ? `${SIGN_IN_PATH}?${RETURN_PARAM}=${encodeURIComponent(current)}` : SIGN_IN_PATH;
}

/** The page to open after signing in, or null when the value is empty or is not a page of this app. */
export function safeReturnPath(raw: string | null | undefined): string | null {
	if (!raw || !raw.startsWith('/') || raw.startsWith('//') || raw.includes('\\')) return null;
	// A path with a control character or a scheme-like start could be read as another address.
	if (/[\u0000-\u001f]/.test(raw)) return null;
	return APP_ROOTS.some((root) => raw === root.replace(/\/$/, '') || raw.startsWith(root)) ? raw : null;
}
