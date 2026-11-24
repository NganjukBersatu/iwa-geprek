/** The content-security-policy of the web: one definition, read by the Vite config (the policy) and the server hook (where the reports go). */
export const REPORT_PATH = '/api/csp-reports';
export const REPORT_GROUP = 'csp';

/** The policy the web keeps. Inline styles are never allowed: values go through the style object (the dynamicStyle action) and the one inline style SvelteKit writes itself is allowed by its hash. */
export const policy: Record<string, string[]> = {
	'default-src': ['self'],
	'script-src': ['self'],
	'style-src': ['self'],
	'img-src': ['self', 'data:', 'blob:', 'https:'],
	'media-src': ['self', 'blob:', 'https:'],
	'font-src': ['self', 'data:'],
	'connect-src': ['self'],
	'worker-src': ['self'],
	'manifest-src': ['self'],
	'object-src': ['none'],
	'base-uri': ['self'],
	'form-action': ['self'],
	'frame-ancestors': ['none']
};
