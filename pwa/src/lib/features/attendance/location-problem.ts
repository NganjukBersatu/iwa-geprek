import type { LocationReading } from '$lib/platform/location';
import { t } from '$lib/text/t';

/** Kalimat penyebab dan langkah perbaikan untuk bacaan lokasi yang gagal; null bila bacaan berhasil. */
export function locationProblemText(reading: LocationReading): string | null {
	switch (reading.kind) {
		case 'fix':
			return null;
		case 'denied':
			return t('web_location_denied');
		case 'timeout':
			return t('web_location_timeout');
		case 'unavailable':
			return t('web_location_unavailable');
	}
}
