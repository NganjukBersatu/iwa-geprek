import * as echarts from 'echarts/core';
import { BarChart, HeatmapChart, LineChart, ScatterChart } from 'echarts/charts';
import { GridComponent, LegendComponent, TooltipComponent, VisualMapComponent } from 'echarts/components';
import { LegacyGridContainLabel } from 'echarts/features';
import { CanvasRenderer } from 'echarts/renderers';

let registered = false;

/** Jenis seri, komponen, dan penyaji yang dipakai grafik; yang tidak didaftarkan di sini tidak tampil. */
function registerParts(): void {
	if (registered) return;
	// LegacyGridContainLabel menjaga tata letak sumbu yang sama dengan paket ECharts utuh.
	echarts.use([BarChart, HeatmapChart, LineChart, ScatterChart, GridComponent, LegendComponent, TooltipComponent, VisualMapComponent, LegacyGridContainLabel, CanvasRenderer]);
	registered = true;
}

export function createChart(container: HTMLElement) {
	registerParts();
	return echarts.init(container, undefined, { renderer: 'canvas' });
}
