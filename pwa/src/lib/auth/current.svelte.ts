import { clearSession, loadSession, profileOf, saveSession, type LoginSession } from './session';
import { ApiCaller } from '$lib/api/http';
import type { UserOut } from '$lib/api/types';

const LOGOUT_PATH = '/v2/auth/logout';
const ME_PATH = '/v2/auth/me';

/** Sesi yang sedang berlaku; satu-satunya tempat halaman membaca siapa yang masuk dan memanggil API atas namanya. */
class CurrentSession {
	session = $state<LoginSession | null>(null);
	/** Benar setelah sesi tersimpan selesai dibaca, sebelum itu layar pembuka belum boleh membuka isi. */
	restored = $state(false);

	async restore(): Promise<void> {
		this.session = loadSession() ?? (await this.fromCookie());
		this.restored = true;
	}

	/** No usable copy on this device (storage refused in private browsing, cleared, or from an earlier release): the cookie may still sign this browser in. */
	private async fromCookie(): Promise<LoginSession | null> {
		const result = await new ApiCaller().read<UserOut>(ME_PATH);
		return result.kind === 'success' ? { user: profileOf(result.value) } : null;
	}

	signIn(session: LoginSession, expiresInSeconds: number): void {
		this.session = session;
		saveSession(session, expiresInSeconds);
	}

	/** Melupakan sesi di halaman saja, misalnya setelah server menolaknya. */
	signOut(): void {
		this.session = null;
		clearSession();
	}

	/** Keluar atas pilihan karyawan: halaman baru melupakan sesi setelah server mencabutnya atau sudah menolaknya, jadi cookie tidak pernah tertinggal hidup; false bila gagal. */
	async logOut(): Promise<boolean> {
		const result = await new ApiCaller().write('POST', LOGOUT_PATH);
		if (result.kind === 'failure') return false;
		this.signOut();
		return true;
	}

	/** Pemanggil API untuk sesi ini; hanya dipakai saat sudah masuk. */
	api(): ApiCaller {
		if (!this.session) throw new Error('Belum masuk');
		return new ApiCaller();
	}
}

export const current = new CurrentSession();
