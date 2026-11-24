/** Fills the {name} places of a sentence; a name with no value is left as it is, so a missing value shows up instead of vanishing. */
export function format(template: string, params: Record<string, string | number> = {}): string {
	return template.replace(/\{(\w+)\}/g, (placeholder, name: string) => (name in params ? String(params[name]) : placeholder));
}
