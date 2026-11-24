import { api } from "$lib/api";
import type { ExtraReport, VariantReport, VariantRow } from "$lib/api/types";
import { createReportFilters } from "../report/filters";
import {
  rangeParams,
  ReportState,
  type ReportQuery,
} from "../report/report.svelte";
import { ListSort, sortKeys } from "$lib/components/table/list-sort.svelte";
import { extraColumns, variantColumns } from "./columns";
import { termText } from '$lib/text/terms';
import { variantReportText } from '$lib/text/variant-report';

export type VariantQuery = ReportQuery & { perMenu: boolean };

export type VariantData = VariantReport & { extras: ExtraReport };

export class VariantState extends ReportState<VariantQuery, VariantData> {
  readonly variantSort = new ListSort(
    "varian",
    sortKeys(variantColumns(false)),
    () => void this.queryChanged(this.query),
  );
  readonly extraSort = new ListSort(
    "ekstra",
    sortKeys(extraColumns),
    () => void this.queryChanged(this.query),
  );

  filters = createReportFilters([
    {
      kind: "select",
      key: "bagian",
      label: variantReportText.part,
      options: [
        { value: "varian", label: variantReportText.variant },
        { value: "ekstra", label: termText.extra },
      ],
    },
    {
      kind: "select",
      key: "pecah",
      label: variantReportText.splitPerMenu,
      options: [{ value: "ya", label: termText.yes }],
    },
  ]);

  get query(): VariantQuery {
    return {
      branch: this.filters.get("cabang"),
      range: this.filters.range("rentang"),
      perMenu: this.filters.get("pecah") === "ya",
    };
  }

  get section(): "varian" | "ekstra" {
    return this.filters.get("bagian") === "ekstra" ? "ekstra" : "varian";
  }

  get variants(): VariantReport | null {
    return this.data;
  }

  get extras(): ExtraReport | null {
    return this.data?.extras ?? null;
  }

  get groups(): [string, VariantRow[]][] {
    const map = new Map<string, VariantRow[]>();
    for (const row of this.data?.rows ?? [])
      map.set(row.group, [...(map.get(row.group) ?? []), row]);
    return [...map.entries()];
  }

  protected async fetch(query: VariantQuery): Promise<VariantData> {
    const range = rangeParams(query.range);
    const [variants, extras] = await Promise.all([
      api.reports.variants({
        ...range,
        by_menu: query.perMenu,
        sort: this.variantSort.param,
      }),
      api.reports.extras({ ...range, sort: this.extraSort.param }),
    ]);
    return { ...variants, extras };
  }
}
