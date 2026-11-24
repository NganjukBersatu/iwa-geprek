import { createReadStream } from 'node:fs';
import { stat } from 'node:fs/promises';
import { resolve } from 'node:path';
import { Readable } from 'node:stream';
import { error } from '@sveltejs/kit';
import type { RequestHandler } from './$types';
import { APK_NAME } from '$lib/features/download/release';
import { downloadText } from '$lib/text/download';

/** Outside static on purpose: the static server sends .apk without a type, so some browsers save it as .zip. */
const APK_FOLDER = resolve('apk');
const APK_TYPE = 'application/vnd.android.package-archive';

export const GET: RequestHandler = async ({ params }) => {
	if (params.file !== APK_NAME) error(404, downloadText.apkNotFound);
	const path = resolve(APK_FOLDER, APK_NAME);
	const file = await stat(path).catch(() => null);
	if (!file?.isFile()) error(404, downloadText.apkNotFound);

	return new Response(Readable.toWeb(createReadStream(path)) as ReadableStream<Uint8Array>, {
		headers: {
			'Content-Type': APK_TYPE,
			'Content-Length': String(file.size),
			'Content-Disposition': `attachment; filename="${APK_NAME}"; filename*=UTF-8''${encodeURIComponent(APK_NAME)}`,
			'Cache-Control': 'public, max-age=300'
		}
	});
};
