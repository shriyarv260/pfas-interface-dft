"""Strict, preregistered numerical reproduction checks, not universal DFT accuracy."""

import math


def evaluate(references, predictions, policy):
    if not references:
        raise ValueError("Empty reference set")
    if not (0 < policy["target_fraction"] <= 1) or policy["minimum_cases"] < 1:
        raise ValueError("Invalid benchmark policy")
    refs = {r["id"]: r for r in references}
    preds = {p["id"]: p for p in predictions}
    if len(refs) != len(references) or len(preds) != len(predictions):
        raise ValueError("Duplicate benchmark IDs")
    if set(preds) - set(refs):
        raise ValueError("Predictions contain unknown benchmark IDs")
    for r in references:
        if r["quantity"] not in {
            "barrier_ev",
            "reaction_energy_ev",
            "barrier_change_ev",
            "reaction_energy_change_ev",
        }:
            raise ValueError("Only energy differences qualify, not absolute total energies")
        if (
            not math.isfinite(r["value_ev"])
            or not math.isfinite(r["tolerance_ev"])
            or r["tolerance_ev"] <= 0
        ):
            raise ValueError("Invalid benchmark value or tolerance")
        if not r["source_id"] or not r["condition_id"] or not r["independence_group"]:
            raise ValueError("Missing provenance or conditions")
    checks, errors = [], []
    for key, ref in refs.items():
        pred = preds.get(key)
        row = {"id": key, "passed": False}
        if pred is None:
            row["reason"] = "missing_prediction"
        elif pred.get("status") != "computed" or pred.get("converged") is not True:
            row["reason"] = "not_a_converged_computation"
        elif (
            pred.get("condition_id") != ref["condition_id"]
            or pred.get("quantity") != ref["quantity"]
        ):
            row["reason"] = "incompatible_conditions_or_quantity"
        elif (
            not pred.get("artifact_sha256")
            or len(pred["artifact_sha256"]) != 64
            or any(c not in "0123456789abcdef" for c in pred["artifact_sha256"])
        ):
            row["reason"] = "missing_or_invalid_result_hash"
        else:
            value = float(pred["value_ev"])
            if not math.isfinite(value):
                raise ValueError("Nonfinite prediction")
            error = abs(value - ref["value_ev"])
            errors.append(error)
            row.update(
                error_ev=error,
                passed=error <= ref["tolerance_ev"] + 1e-12,
                reason="within_tolerance"
                if error <= ref["tolerance_ev"] + 1e-12
                else "outside_tolerance",
            )
        checks.append(row)
    n = len(refs)
    passed = sum(r["passed"] for r in checks)
    fraction = passed / n  # Missing cases stay in the denominator.
    z = 1.959963984540054
    center = (fraction + z * z / (2 * n)) / (1 + z * z / n)
    radius = z * math.sqrt(fraction * (1 - fraction) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    independent = len({r["independence_group"] for r in references})
    eligible = independent >= policy["minimum_cases"] and len(errors) == n
    return {
        "status": "target_met"
        if eligible and fraction >= policy["target_fraction"]
        else "not_validated",
        "target_fraction": policy["target_fraction"],
        "n_reference": n,
        "n_independence_groups": independent,
        "n_eligible_predictions": len(errors),
        "n_passed": passed,
        "fraction_within_tolerance": fraction,
        "mae_ev": sum(errors) / len(errors) if errors else None,
        "rmse_ev": math.sqrt(sum(e * e for e in errors) / len(errors)) if errors else None,
        "wilson_95_interval_descriptive_only": [max(0, center - radius), min(1, center + radius)],
        "checks": checks,
        "limitations": "Condition matching and independence require scientific review. A hash is a provenance pointer, not proof. Correlated cases invalidate binomial inference. This metric is numerical reproduction, not degradation efficiency or general DFT accuracy.",
    }
