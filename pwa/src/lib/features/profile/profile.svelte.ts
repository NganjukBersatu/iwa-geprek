import type { Schemas } from '$lib/api/contract';
import { current } from '$lib/auth/current.svelte';
import { failureText, type AppFailure } from '$lib/failure/failure';
import { t } from '$lib/text/t';

type ProfileResponse = Schemas['ProfileOut'];

const PROFILE = '/v2/profile';
export const MIN_PASSWORD_LENGTH = 15;
const PHOTO_FIELD = 'file';
const PHOTO_NAME = 'foto.jpg';

export type ProfileDetail = {
	name: string;
	username: string;
	roleName: string;
	outletName: string | null;
	/** Tanggal "YYYY-MM-DD". */
	joinedDate: string | null;
	birthDate: string | null;
	phone: string;
	address: string;
	email: string;
	/** "L" atau "P"; null bila belum diisi. */
	gender: string | null;
	emergencyName: string;
	emergencyPhone: string;
	emergencyRelation: string;
	photoUrl: string | null;
};

/** Isian formulir data diri yang bisa diubah. */
export type ProfileForm = Omit<ProfileDetail, 'username' | 'roleName' | 'outletName' | 'joinedDate' | 'birthDate' | 'photoUrl'>;

export type FormMessage = { text: string; success: boolean };

const detailOf = (dto: ProfileResponse): ProfileDetail => ({
	name: dto.name?.trim() || dto.username,
	username: dto.username,
	roleName: dto.role_name,
	outletName: dto.outlet_name,
	joinedDate: dto.joined_date,
	birthDate: dto.birth_date,
	phone: dto.phone ?? '',
	address: dto.address ?? '',
	email: dto.email ?? '',
	gender: dto.gender,
	emergencyName: dto.emergency_name ?? '',
	emergencyPhone: dto.emergency_phone ?? '',
	emergencyRelation: dto.emergency_relation ?? '',
	photoUrl: dto.photo_url
});

const formOf = (detail: ProfileDetail): ProfileForm => ({
	name: detail.name,
	phone: detail.phone,
	address: detail.address,
	email: detail.email,
	gender: detail.gender,
	emergencyName: detail.emergencyName,
	emergencyPhone: detail.emergencyPhone,
	emergencyRelation: detail.emergencyRelation
});

const emptyForm = (): ProfileForm => ({ name: '', phone: '', address: '', email: '', gender: null, emergencyName: '', emergencyPhone: '', emergencyRelation: '' });

/** Keadaan halaman Profil: data akun, formulir data diri, ganti sandi, dan foto profil. */
export class ProfileState {
	detail = $state<ProfileDetail | null>(null);
	loading = $state(true);
	failure = $state<AppFailure | null>(null);
	form = $state<ProfileForm>(emptyForm());
	saving = $state(false);
	saveMessage = $state<FormMessage | null>(null);
	oldPassword = $state('');
	newPassword = $state('');
	confirmPassword = $state('');
	changingPassword = $state(false);
	passwordMessage = $state<FormMessage | null>(null);
	uploadingPhoto = $state(false);
	photoError = $state<string | null>(null);

	constructor(private readonly onSessionExpired: () => void) {}

	async load(): Promise<void> {
		this.loading = true;
		this.failure = null;
		const result = await current.api().read<ProfileResponse>(PROFILE);
		if (result.kind === 'unauthorized') return this.onSessionExpired();
		this.loading = false;
		if (result.kind === 'failure') {
			this.failure = result.failure;
			return;
		}
		this.detail = detailOf(result.value);
		this.form = formOf(this.detail);
	}

	/** Ubah isian; pesan hasil simpan sebelumnya dibersihkan. */
	edit(change: Partial<ProfileForm>): void {
		this.form = { ...this.form, ...change };
		this.saveMessage = null;
	}

	setOldPassword(value: string): void {
		this.oldPassword = value;
		this.passwordMessage = null;
	}

	setNewPassword(value: string): void {
		this.newPassword = value;
		this.passwordMessage = null;
	}

	setConfirmPassword(value: string): void {
		this.confirmPassword = value;
		this.passwordMessage = null;
	}

	async save(): Promise<void> {
		if (this.saving) return;
		if (this.form.name.trim() === '') {
			this.saveMessage = { text: t('profile_name_required'), success: false };
			return;
		}
		this.saving = true;
		this.saveMessage = null;
		// Semua field dikirim agar kolom yang dikosongkan ikut terhapus di server.
		const body = {
			name: this.form.name.trim(),
			phone: this.form.phone.trim(),
			address: this.form.address.trim(),
			email: this.form.email.trim(),
			gender: this.form.gender,
			emergency_name: this.form.emergencyName.trim(),
			emergency_phone: this.form.emergencyPhone.trim(),
			emergency_relation: this.form.emergencyRelation.trim()
		};
		const result = await current.api().write<ProfileResponse>('PATCH', PROFILE, body);
		if (result.kind === 'unauthorized') return this.onSessionExpired();
		this.saving = false;
		if (result.kind === 'failure') {
			this.saveMessage = { text: failureText(result.failure), success: false };
			return;
		}
		this.detail = detailOf(result.value);
		this.form = formOf(this.detail);
		this.saveMessage = { text: t('profile_saved'), success: true };
	}

	async changePassword(): Promise<void> {
		if (this.changingPassword) return;
		if (this.newPassword.length < MIN_PASSWORD_LENGTH) {
			this.passwordMessage = { text: t('password_too_short'), success: false };
			return;
		}
		if (this.newPassword !== this.confirmPassword) {
			this.passwordMessage = { text: t('password_mismatch'), success: false };
			return;
		}
		this.changingPassword = true;
		this.passwordMessage = null;
		const result = await current.api().write('POST', `${PROFILE}/password`, { current_password: this.oldPassword, new_password: this.newPassword });
		if (result.kind === 'unauthorized') return this.onSessionExpired();
		this.changingPassword = false;
		if (result.kind === 'failure') {
			this.passwordMessage = { text: failureText(result.failure), success: false };
			return;
		}
		this.oldPassword = '';
		this.newPassword = '';
		this.confirmPassword = '';
		this.passwordMessage = { text: t('password_changed'), success: true };
	}

	/** Mengganti foto profil; mengembalikan true setelah berhasil agar lembarnya menutup. */
	async uploadPhoto(photo: Blob): Promise<boolean> {
		if (this.uploadingPhoto) return false;
		this.uploadingPhoto = true;
		this.photoError = null;
		const body = new FormData();
		body.append(PHOTO_FIELD, photo, PHOTO_NAME);
		const result = await current.api().write<ProfileResponse>('PUT', `${PROFILE}/photo`, body);
		if (result.kind === 'unauthorized') {
			this.onSessionExpired();
			return false;
		}
		this.uploadingPhoto = false;
		if (result.kind === 'failure') {
			this.photoError = failureText(result.failure);
			return false;
		}
		if (this.detail) this.detail = { ...this.detail, photoUrl: detailOf(result.value).photoUrl };
		return true;
	}

	/** Menghapus foto profil lalu membaca ulang profil tanpa menimpa isian yang sedang diubah. */
	async deletePhoto(): Promise<boolean> {
		if (this.uploadingPhoto) return false;
		this.uploadingPhoto = true;
		this.photoError = null;
		const result = await current.api().write('DELETE', `${PROFILE}/photo`);
		if (result.kind === 'unauthorized') {
			this.onSessionExpired();
			return false;
		}
		if (result.kind === 'failure') {
			this.uploadingPhoto = false;
			this.photoError = failureText(result.failure);
			return false;
		}
		const fresh = await current.api().read<ProfileResponse>(PROFILE);
		if (fresh.kind === 'success' && this.detail) this.detail = { ...this.detail, photoUrl: detailOf(fresh.value).photoUrl };
		this.uploadingPhoto = false;
		return true;
	}

	clearPhotoError(): void {
		this.photoError = null;
	}
}
