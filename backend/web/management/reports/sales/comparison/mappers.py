"""Turns the comparison into its response schema."""
from web.management.reports.sales.comparison.domain import Comparison
from web.management.reports.sales.comparison.schemas import ComparisonOut


def comparison_out(comparison: Comparison) -> ComparisonOut:
    return ComparisonOut.model_validate(comparison)
