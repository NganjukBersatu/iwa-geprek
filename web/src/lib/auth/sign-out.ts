import { api } from '$lib/api';
import { ApiError } from '$lib/api/http';
import { authText } from '$lib/text/auth';
import { clearSession } from './session';

export const SIGN_OUT_FAILED = authText.signOutFailed;

/** The page forgets the account only once the server has ended this sign-in or already refuses it, so a failed call never leaves a live cookie behind the login screen. */
export async function endSignIn(): Promise<boolean> {
	try {
		await api.auth.logout();
	} catch (problem) {
		if (!(problem instanceof ApiError && problem.status === 401)) return false;
	}
	clearSession();
	return true;
}
