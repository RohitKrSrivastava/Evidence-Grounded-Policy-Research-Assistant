"""Deterministic calculation engine and dataset querying tools for agentic policy workflow."""
import math
from typing import Dict, Any, List, Optional
import pandas as pd
from src.schema import CalculationStep
from src.config import STRUCTURED_DATA_DIR

class DeterministicCalculator:
    """Safe arithmetic execution without LLM calculation hallucination."""

    @staticmethod
    def calculate_cagr(start_val: float, end_val: float, num_years: float) -> CalculationStep:
        """Calculates Compound Annual Growth Rate: ((end / start) ** (1 / n) - 1) * 100."""
        if start_val <= 0 or end_val <= 0 or num_years <= 0:
            raise ValueError("CAGR inputs must be positive numbers and years > 0.")

        cagr = (math.pow(end_val / start_val, 1.0 / num_years) - 1.0) * 100.0
        return CalculationStep(
            operation="CAGR",
            expression=f"(({end_val} / {start_val}) ** (1 / {num_years}) - 1) * 100",
            inputs={"start_val": start_val, "end_val": end_val, "years": num_years},
            result=round(cagr, 2),
            formatted_result=f"{round(cagr, 2)}%"
        )

    @staticmethod
    def calculate_percentage_growth(old_val: float, new_val: float) -> CalculationStep:
        """Calculates Percentage Growth: ((new - old) / old) * 100."""
        if old_val == 0:
            raise ZeroDivisionError("Base value cannot be zero for percentage growth.")

        growth = ((new_val - old_val) / abs(old_val)) * 100.0
        return CalculationStep(
            operation="PERCENTAGE_GROWTH",
            expression=f"(({new_val} - {old_val}) / {old_val}) * 100",
            inputs={"old_val": old_val, "new_val": new_val},
            result=round(growth, 2),
            formatted_result=f"{round(growth, 2)}%"
        )

    @staticmethod
    def calculate_difference(val_a: float, val_b: float, unit: str = "") -> CalculationStep:
        """Calculates Difference: val_a - val_b."""
        diff = val_a - val_b
        return CalculationStep(
            operation="DIFFERENCE",
            expression=f"{val_a} - {val_b}",
            inputs={"val_a": val_a, "val_b": val_b},
            result=round(diff, 2),
            formatted_result=f"{round(diff, 2)} {unit}".strip()
        )

    @staticmethod
    def calculate_ratio(numerator: float, denominator: float) -> CalculationStep:
        """Calculates Ratio: numerator / denominator."""
        if denominator == 0:
            raise ZeroDivisionError("Denominator cannot be zero.")

        ratio = numerator / denominator
        return CalculationStep(
            operation="RATIO",
            expression=f"{numerator} / {denominator}",
            inputs={"numerator": numerator, "denominator": denominator},
            result=round(ratio, 4),
            formatted_result=f"{round(ratio, 2)}x"
        )

class DatasetQueryTool:
    """Deterministic querying engine for structured tabular government statistics."""

    def __init__(self):
        self.macro_df = pd.read_csv(STRUCTURED_DATA_DIR / "sg_digital_economy_macro.csv")
        self.talent_df = pd.read_csv(STRUCTURED_DATA_DIR / "tech_talent_workforce.csv")
        self.sme_df = pd.read_csv(STRUCTURED_DATA_DIR / "sme_digital_adoption.csv")

    def query_macro(self, metric: str, year: Optional[int] = None) -> List[Dict[str, Any]]:
        """Queries macroeconomic indicators."""
        df = self.macro_df[self.macro_df["metric"].str.contains(metric, case=False, na=False)]
        if year:
            df = df[df["year"] == year]
        return df.to_dict(orient="records")

    def query_workforce(self, role: str, year: Optional[int] = None) -> List[Dict[str, Any]]:
        """Queries workforce statistics for a given role category."""
        df = self.talent_df[self.talent_df["role_category"].str.contains(role, case=False, na=False)]
        if year:
            df = df[df["year"] == year]
        return df.to_dict(orient="records")

    def query_sme_adoption(self, sector: str, year: Optional[int] = None) -> List[Dict[str, Any]]:
        """Queries SME digital adoption stats by industry sector."""
        df = self.sme_df[self.sme_df["sector"].str.contains(sector, case=False, na=False)]
        if year:
            df = df[df["year"] == year]
        return df.to_dict(orient="records")

class FlakyToolSimulator:
    """Tool that fails intentionally on initial call to verify agent retry & failure recovery."""

    def __init__(self, fail_first_n_times: int = 1):
        self.fail_limit = fail_first_n_times
        self.call_count = 0

    def query_external_registry(self, query_param: str) -> Dict[str, Any]:
        self.call_count += 1
        if self.call_count <= self.fail_limit:
            raise ConnectionError(f"Simulated network timeout connecting to remote registry (attempt {self.call_count}/{self.fail_limit})")

        return {
            "status": "SUCCESS",
            "recovered_at_attempt": self.call_count,
            "data": f"Validated registry record for: {query_param}"
        }
