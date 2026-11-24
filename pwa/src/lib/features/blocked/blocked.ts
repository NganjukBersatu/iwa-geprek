import { brand } from '$lib/brand/brand';
import { t } from '$lib/text/t';

/** Isi layar penolakan untuk semua perangkat selain iPhone dan iPad, dipakai halaman dari server dan layar cadangan di browser agar keduanya sama. */
export const BLOCKED_TEXT = {
	title: t('web_blocked_title'),
	body: t('web_blocked_body')
};

export const BLOCKED_LOGO = '/brand-logo.png';

/** Halaman penolakan yang dikirim server sebelum aplikasi termuat; warna dan ukuran mengikuti token app.css. */
export function blockedPageHtml(): string {
	return `<!doctype html><html lang="id"><head><meta charset="utf-8" /><meta name="viewport" content="width=device-width, initial-scale=1" /><meta name="theme-color" content="${brand.colors.page}" /><title>${brand.name}</title></head><body style="margin:0;min-height:100vh;display:flex;align-items:center;justify-content:center;background:${brand.colors.page};color:${brand.colors.ink};font-family:system-ui,-apple-system,'Segoe UI',Roboto,'Helvetica Neue',Arial,sans-serif"><main style="display:flex;flex-direction:column;align-items:center;gap:16px;width:100%;max-width:360px;padding:24px;box-sizing:border-box;text-align:center"><img src="${BLOCKED_LOGO}" alt="" style="width:144px;height:auto" /><h1 style="margin:0;font-size:26px;line-height:32px;font-weight:700">${BLOCKED_TEXT.title}</h1><p style="margin:0;font-size:16px;line-height:22px;color:${brand.colors.muted}">${BLOCKED_TEXT.body}</p></main></body></html>`;
}
