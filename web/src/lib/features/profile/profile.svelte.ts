import { userMessage } from '$lib/api/user-message';
import { api } from '$lib/api';
import { ApiError } from '$lib/api/http';
import type { Profile, ProfileUpdate } from '$lib/api/types';
import { getUser, saveUser } from '$lib/auth/session';
import { toast } from '$lib/components/feedback/toast.svelte';
import { profileText } from '$lib/text/profile';


const reason = (error: unknown, fallback: string) => (userMessage(error, fallback));

/** Whether a save worked, and the sentence for the person when it did not. */
export type SaveResult = { ok: boolean; message: string };

/** The signed-in person's own account: details, photo, and password. */
export class ProfileState {
	profile = $state<Profile | null>(null);
	loading = $state(true);
	error = $state('');
	saving = $state(false);
	photoBusy = $state(false);
	changingPassword = $state(false);
	/** What the server refused about the details and about the password, by field name. */
	fieldErrors = $state<Record<string, string>>({});
	passwordFieldErrors = $state<Record<string, string>>({});
	/** Counts loads and saves of the details, so the form refills then and not when only the photo changed. */
	revision = $state(0);

	async load(): Promise<void> {
		this.loading = true;
		this.error = '';
		try {
			this.apply(await api.profile.read());
			this.revision += 1;
		} catch (error) {
			this.error = reason(error, profileText.loadFailed);
		} finally {
			this.loading = false;
		}
	}

	/** The copy of the account kept in this browser follows, so the sidebar shows the new name and photo. */
	private apply(profile: Profile): void {
		this.profile = profile;
		const user = getUser();
		if (user) saveUser({ ...user, name: profile.name, photo_url: profile.photo_url });
	}

	async save(body: ProfileUpdate): Promise<SaveResult> {
		this.saving = true;
		this.fieldErrors = {};
		try {
			this.apply(await api.profile.update(body));
			this.revision += 1;
			toast.show(profileText.saved);
			return { ok: true, message: '' };
		} catch (error) {
			this.fieldErrors = error instanceof ApiError ? error.fieldErrors : {};
			return { ok: false, message: reason(error, profileText.saveFailed) };
		} finally {
			this.saving = false;
		}
	}

	async changePassword(current: string, next: string): Promise<SaveResult> {
		this.changingPassword = true;
		this.passwordFieldErrors = {};
		try {
			await api.profile.changePassword(current, next);
			toast.show(profileText.passwordChanged);
			return { ok: true, message: '' };
		} catch (error) {
			this.passwordFieldErrors = error instanceof ApiError ? error.fieldErrors : {};
			return { ok: false, message: reason(error, profileText.passwordChangeFailed) };
		} finally {
			this.changingPassword = false;
		}
	}

	/** The file comes from PhotoField, already converted and shrunk. */
	async setPhoto(file: File): Promise<string> {
		this.photoBusy = true;
		try {
			this.apply(await api.profile.uploadPhoto(file));
			toast.show(profileText.photoReplaced);
			return '';
		} catch (error) {
			return reason(error, profileText.photoUploadFailed);
		} finally {
			this.photoBusy = false;
		}
	}

	async removePhoto(): Promise<string> {
		this.photoBusy = true;
		try {
			await api.profile.removePhoto();
			if (this.profile) this.apply({ ...this.profile, photo_url: null });
			toast.show(profileText.photoRemoved);
			return '';
		} catch (error) {
			return reason(error, profileText.photoRemoveFailed);
		} finally {
			this.photoBusy = false;
		}
	}
}
