import { goto } from '$app/navigation';
import { api } from '$lib/api';
import { userMessage } from '$lib/api/user-message';
import { mayEnterWeb, saveSession } from '$lib/auth/session';
import { PAGES } from '$lib/nav/pages';
import { safeReturnPath } from '$lib/nav/return-to';
import { authText } from '$lib/text/auth';

export type LoginField = 'username' | 'password';

/** Signing in to the management web: an account the server keeps out of the web never gets a saved session. */
export class LoginState {
	username = $state('');
	password = $state('');
	message = $state('');
	submitting = $state(false);
	/** A field's message shows only once it was left or was the first one found empty on send. */
	#touched = $state<Record<LoginField, boolean>>({ username: false, password: false });
	/** The page the person was on before being sent here; only a page of this app is used, otherwise the dashboard opens. */
	readonly #returnTo: string | null;

	constructor(returnTo: string | null) {
		this.#returnTo = safeReturnPath(returnTo);
	}

	usernameError = $derived(this.#touched.username && this.username.trim() === '' ? authText.login.username.required : '');
	passwordError = $derived(this.#touched.password && this.password === '' ? authText.login.password.required : '');

	touch(field: LoginField): void {
		this.#touched[field] = true;
	}

	/** Returns the first field that needs filling, or null when the form can be sent. */
	validate(): LoginField | null {
		const empty: LoginField | null = this.username.trim() === '' ? 'username' : this.password === '' ? 'password' : null;
		if (empty) this.touch(empty);
		return empty;
	}

	async submit(): Promise<void> {
		this.message = '';
		this.submitting = true;
		try {
			const result = await api.auth.login(this.username, this.password);
			if (!mayEnterWeb(result.user)) {
				this.message = authText.login.noWebAccess;
				return;
			}
			saveSession(result.user);
			await goto(this.#returnTo ?? PAGES.dashboard.path);
		} catch (error) {
			this.message = userMessage(error);
		} finally {
			this.submitting = false;
		}
	}
}
