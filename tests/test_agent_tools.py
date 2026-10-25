"""Tests for deterministic calculations, dataset querying, and tool recovery."""
import pytest
from src.agent.tools import DeterministicCalculator, DatasetQueryTool, FlakyToolSimulator
from src.agent.workflow import PolicyAgentWorkflow
from src.agent.state import AgentPhase

def test_deterministic_cagr_calculation():
    # ((38.6 / 19.2) ** (1 / 5) - 1) * 100 = 14.99%
    calc = DeterministicCalculator.calculate_cagr(19.2, 38.6, 5.0)
    assert calc.operation == "CAGR"
    assert calc.result == 14.99
    assert calc.formatted_result == "14.99%"

def test_cagr_invalid_inputs():
    with pytest.raises(ValueError):
        DeterministicCalculator.calculate_cagr(-10.0, 50.0, 2.0)
    with pytest.raises(ValueError):
        DeterministicCalculator.calculate_cagr(10.0, 50.0, 0.0)

def test_percentage_growth_calculation():
    # 12000 to 24500 -> ((24500 - 12000) / 12000) * 100 = 104.17%
    calc = DeterministicCalculator.calculate_percentage_growth(12000.0, 24500.0)
    assert calc.result == 104.17
    assert calc.formatted_result == "104.17%"

def test_difference_calculation():
    calc = DeterministicCalculator.calculate_difference(56.0, 14.8, unit="percentage points")
    assert calc.result == 41.2
    assert "41.2 percentage points" in calc.formatted_result

def test_dataset_query_tool():
    tool = DatasetQueryTool()
    macro_records = tool.query_macro("Value Added", year=2023)
    assert len(macro_records) == 1
    assert macro_records[0]["value"] == 38.6

    talent_records = tool.query_workforce("Data Scientists", year=2023)
    assert len(talent_records) == 1
    assert talent_records[0]["employment_count"] == 24500

def test_flaky_tool_retry_recovery():
    flaky = FlakyToolSimulator(fail_first_n_times=2)
    # Attempt 1 -> fails
    with pytest.raises(ConnectionError):
        flaky.query_external_registry("test_token")
    # Attempt 2 -> fails
    with pytest.raises(ConnectionError):
        flaky.query_external_registry("test_token")
    # Attempt 3 -> succeeds
    res = flaky.query_external_registry("test_token")
    assert res["status"] == "SUCCESS"
    assert res["recovered_at_attempt"] == 3
