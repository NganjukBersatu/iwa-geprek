import { ApiCaller } from '$lib/api/http';

const VERSION_PATH = '/v2/client-version';
const VERSION_PATTERN = /^(\d{1,4})\.(\d{1,4})\.(\d{1,4})$/;

type ClientVersionDto = { apk_minimum: string | null; pwa_minimum: string | null; download_url: string | null };

function parsed(value: string): [number, number, number] | null {
	const found = VERSION_PATTERN.exec(value.trim());
	return found ? [Number(found[1]), Number(found[2]), Number(found[3])] : null;
}

/** True bila [current] di bawah [minimum]; versi yang tidak terbaca tidak pernah mengunci siapa pun. */
export function isBelow(current: string, minimum: string): boolean {
	const have = parsed(current);
	const need = parsed(minimum);
	if (!have || !need) return false;
	const [haveMajor, haveMinor, havePatch] = have;
	const [needMajor, needMinor, needPatch] = need;
	if (haveMajor !== needMajor) return haveMajor < needMajor;
	if (haveMinor !== needMinor) return haveMinor < needMinor;
	return havePatch < needPatch;
}

/** Keadaan "versi ini sudah tidak didukung": diisi saat server menolak (426) atau saat pemeriksaan versi minimum, lalu dibaca lembar pembaruan wajib. */
class UpdateRequired {
	/** Naik setiap penolakan, supaya lembar yang sudah ditunda muncul lagi pada penolakan berikutnya. */
	count = $state(0);
	downloadUrl = $state<string | null>(null);
	minimum = $state<string | null>(null);

	get required(): boolean {
		return this.count > 0;
	}

	require(url: string | null, minimum: string | null = this.minimum): void {
		this.downloadUrl = url;
		this.minimum = minimum;
		this.count += 1;
	}

	/** Dibaca saat aplikasi dibuka, kembali ke layar, atau kembali online; gagal membaca tidak mengubah apa pun. */
	async check(): Promise<void> {
		const result = await new ApiCaller().read<ClientVersionDto>(VERSION_PATH);
		if (result.kind !== 'success') return;
		const minimum = result.value.pwa_minimum;
		if (minimum && isBelow(__APP_VERSION__, minimum)) this.require(result.value.download_url, minimum);
	}
}

export const updateRequired = new UpdateRequired();
