import { anonymousPost } from '$lib/api/http';
import type { SessionOut } from '$lib/api/types';
import { current } from '$lib/auth/current.svelte';
import { profileOf } from '$lib/auth/session';
import { failureText } from '$lib/failure/failure';
import { t } from '$lib/text/t';

// Server menaruh token di cookie yang tidak bisa dibaca skrip; yang kembali hanya akun dan masa berlakunya.
const LOGIN_PATH = '/v2/auth/session';
const STATUS_FORBIDDEN = 403;

/** Keadaan layar masuk: isian, proses kirim, dan galat yang ditampilkan. */
export class LoginState {
	username = $state('');
	password = $state('');
	submitting = $state(false);
	error = $state<string | null>(null);

	readonly canSubmit = $derived(!this.submitting && this.username.trim() !== '' && this.password.trim() !== '');

	clearError(): void {
		this.error = null;
	}

	async submit(): Promise<boolean> {
		if (!this.canSubmit) return false;
		this.submitting = true;
		this.error = null;
		const result = await anonymousPost<SessionOut>(LOGIN_PATH, { username: this.username, password: this.password });
		this.submitting = false;
		if (result.kind === 'success') {
			current.signIn({ user: profileOf(result.value.user) }, result.value.expires_in);
			this.password = '';
			return true;
		}
		if (result.kind === 'unauthorized') this.error = t('failure_login_invalid');
		else if (result.failure.kind === 'rejected' && result.failure.code === STATUS_FORBIDDEN) this.error = result.failure.message ?? t('failure_login_inactive');
		else this.error = failureText(result.failure);
		return false;
	}
}
