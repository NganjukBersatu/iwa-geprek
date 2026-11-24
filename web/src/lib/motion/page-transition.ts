import { onNavigate } from '$app/navigation';
import { motionReduced } from './reduced';

/** Moving to another screen: the old page area (class `page-transition`) drops and fades while the new one comes in; called once by the app layout. */
export function pageTransition(): void {
	onNavigate((navigation) => {
		// Tab yang tersembunyi tidak bisa menjalankan transisi, jadi navigasi berjalan tanpa animasi.
		if (!document.startViewTransition || motionReduced() || document.hidden) return;
		if (navigation.from?.url.pathname === navigation.to?.url.pathname) return;
		return new Promise((resolve) => {
			const transition = document.startViewTransition(async () => {
				resolve();
				await navigation.complete;
			});
			// Transisi yang digugurkan browser menolak promise ini; navigasinya sendiri tetap selesai.
			transition.ready.catch(() => {});
		});
	});
}
