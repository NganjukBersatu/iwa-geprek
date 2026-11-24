type TooltipPoint = { name?: string; axisValueLabel?: string; seriesName?: string; color?: unknown; value?: unknown };

const FALLBACK_COLOR = 'var(--color-content-muted)';

const element = (tag: string, styles: Partial<CSSStyleDeclaration> = {}, text?: string): HTMLElement => {
	const node = document.createElement(tag);
	Object.assign(node.style, styles);
	if (text !== undefined) node.textContent = text;
	return node;
};

/** Tooltip sumbu berupa elemen DOM, bukan teks HTML: gayanya lewat objek gaya, yang CSP ketat izinkan, sedangkan atribut style tidak. */
export function axisTooltip(format: (value: number) => string) {
	return (params: TooltipPoint | TooltipPoint[]): HTMLElement => {
		const points = Array.isArray(params) ? params : [params];
		const box = element('div');
		box.append(element('div', { fontWeight: '600', marginBottom: '4px' }, points[0]?.axisValueLabel ?? points[0]?.name ?? ''));
		for (const point of points) {
			const raw = Array.isArray(point.value) ? point.value[point.value.length - 1] : point.value;
			const amount = Number(raw);
			const row = element('div', { display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '16px' });
			const label = element('span', { display: 'inline-flex', alignItems: 'center', gap: '6px' });
			label.append(element('span', { width: '8px', height: '8px', borderRadius: '9999px', backgroundColor: typeof point.color === 'string' ? point.color : FALLBACK_COLOR }), element('span', {}, point.seriesName ?? ''));
			row.append(label, element('span', { fontWeight: '600' }, Number.isFinite(amount) ? format(amount) : '-'));
			box.append(row);
		}
		return box;
	};
}
