import copy
from pathlib import Path

import pytest

from pfas_dft.benchmark import evaluate
from pfas_dft.common import load_json


def cases(n=20):
    refs = [
        {
            "id": str(i),
            "quantity": "barrier_ev",
            "value_ev": 1.0,
            "tolerance_ev": 0.1,
            "source_id": "fixture",
            "condition_id": str(i),
            "independence_group": str(i),
        }
        for i in range(n)
    ]
    preds = [
        {
            "id": str(i),
            "quantity": "barrier_ev",
            "condition_id": str(i),
            "status": "computed",
            "converged": True,
            "artifact_sha256": "a" * 64,
            "value_ev": 1.05,
        }
        for i in range(n)
    ]
    return refs, preds


POLICY = {"target_fraction": 0.95, "minimum_cases": 20}


def test_target_fraction_and_denominator():
    refs, preds = cases()
    preds[0]["value_ev"] = 1.2
    report = evaluate(refs, preds, POLICY)
    assert report["status"] == "target_met"
    assert report["fraction_within_tolerance"] == 0.95
    assert report["mae_ev"] == pytest.approx((19 * 0.05 + 0.2) / 20)
    assert report["wilson_95_interval_descriptive_only"][0] < 0.95
    report = evaluate(refs, preds[1:], POLICY)
    assert report["status"] == "not_validated"
    assert report["fraction_within_tolerance"] == 0.95
    assert report["checks"][0]["reason"] == "missing_prediction"


@pytest.mark.parametrize(
    "field,value",
    [
        ("status", "synthetic"),
        ("converged", False),
        ("condition_id", "wrong"),
        ("quantity", "reaction_energy_ev"),
        ("artifact_sha256", None),
    ],
)
def test_invalid_prediction_ineligible(field, value):
    refs, preds = cases()
    preds[0][field] = value
    assert evaluate(refs, preds, POLICY)["status"] == "not_validated"


def test_duplicates_unknown_and_nonfinite():
    refs, preds = cases()
    with pytest.raises(ValueError):
        evaluate(refs, preds + [preds[0]], POLICY)
    extra = copy.deepcopy(preds[0])
    extra["id"] = "unknown"
    with pytest.raises(ValueError):
        evaluate(refs, preds + [extra], POLICY)
    preds[0]["value_ev"] = float("nan")
    with pytest.raises(ValueError):
        evaluate(refs, preds, POLICY)


def test_correlated_cases_cannot_inflate_sample_size():
    refs, preds = cases()
    for ref in refs:
        ref["independence_group"] = "one_calculation"
    assert evaluate(refs, preds, POLICY)["status"] == "not_validated"


def test_absolute_total_energies_excluded():
    refs, preds = cases()
    refs[0]["quantity"] = "total_energy_ev"
    with pytest.raises(ValueError):
        evaluate(refs, preds, POLICY)


def test_bundled_references_do_not_claim_accuracy():
    root = Path(__file__).resolve().parents[1]
    refs = load_json(root / "data/benchmarks/references.json")
    report = evaluate(refs, [], POLICY)
    assert report["status"] == "not_validated"
    assert report["n_independence_groups"] == 2
    assert report["mae_ev"] is None
