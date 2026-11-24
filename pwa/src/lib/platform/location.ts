/** Satu pembacaan posisi perangkat; [accuracyMeters] adalah radius ketidakpastiannya. */
export type LocationFix = { latitude: number; longitude: number; accuracyMeters: number };

/** Hasil membaca posisi: berhasil, ditolak izinnya, terlalu lama, atau layanan lokasi tidak memberi jawaban. */
export type LocationReading = { kind: 'fix'; fix: LocationFix } | { kind: 'denied' } | { kind: 'timeout' } | { kind: 'unavailable' };

const READ_TIMEOUT_MILLIS = 15_000;
const EARTH_RADIUS_METERS = 6_371_000;

export function readLocation(): Promise<LocationReading> {
	return new Promise((resolve) => {
		if (!('geolocation' in navigator)) return resolve({ kind: 'unavailable' });
		navigator.geolocation.getCurrentPosition(
			(position) =>
				resolve({
					kind: 'fix',
					fix: { latitude: position.coords.latitude, longitude: position.coords.longitude, accuracyMeters: position.coords.accuracy }
				}),
			(error) => resolve({ kind: error.code === error.PERMISSION_DENIED ? 'denied' : error.code === error.TIMEOUT ? 'timeout' : 'unavailable' }),
			{ enableHighAccuracy: true, timeout: READ_TIMEOUT_MILLIS, maximumAge: 0 }
		);
	});
}

/** Pemeriksaan murah apakah layanan lokasi menyala: memakai bacaan lama yang masih tersimpan; null bila belum bisa dipastikan. */
export function probeLocationService(): Promise<boolean | null> {
	return new Promise((resolve) => {
		if (!('geolocation' in navigator)) return resolve(false);
		navigator.geolocation.getCurrentPosition(
			() => resolve(true),
			(error) => resolve(error.code === error.POSITION_UNAVAILABLE ? false : null),
			{ enableHighAccuracy: false, timeout: 4000, maximumAge: 600_000 }
		);
	});
}

/** Jarak garis lurus dalam meter dari [fix] ke titik, dengan rumus yang sama dengan server. */
export function distanceMeters(fix: LocationFix, latitude: number, longitude: number): number {
	const radians = (degrees: number) => (degrees * Math.PI) / 180;
	const phi1 = radians(fix.latitude);
	const phi2 = radians(latitude);
	const deltaPhi = phi2 - phi1;
	const deltaLambda = radians(longitude - fix.longitude);
	const haversine = Math.sin(deltaPhi / 2) ** 2 + Math.cos(phi1) * Math.cos(phi2) * Math.sin(deltaLambda / 2) ** 2;
	return 2 * EARTH_RADIUS_METERS * Math.asin(Math.sqrt(haversine));
}
