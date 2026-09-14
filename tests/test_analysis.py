import copy

import pytest

from pfas_dft.analysis import summarize


def rows(energies=(-10, -9.2, -10.4)):
    return [
        {
            "run_id": "test",
            "label": "fixture",
            "image": i,
            "energy_ev": e,
            "status": "synthetic",
            "energy_kind": "electronic_energy",
            "ensemble": "fixed_charge",
            "composition": "CF4",
            "charge": 0,
            "method_id": "fixture",
        }
        for i, e in enumerate(energies)
    ]


def test_known_energies_and_shift_invariance():
    a = summarize(rows())[0]
    b = summarize(rows((100, 100.8, 99.6)))[0]
    assert a["sampled_forward_barrier_ev"] == pytest.approx(0.8)
    assert a["reaction_energy_ev"] == pytest.approx(-0.4)
    assert a["sampled_reverse_barrier_ev"] == pytest.approx(1.2)
    assert a["sampled_forward_barrier_ev"] == pytest.approx(b["sampled_forward_barrier_ev"])


@pytest.mark.parametrize(
    "field", ["charge", "method_id", "composition", "ensemble", "energy_kind", "status"]
)
def test_incompatible_images_rejected(field):
    values = rows()
    values[-1][field] = "different"
    with pytest.raises(ValueError):
        summarize(values)


@pytest.mark.parametrize("energies", [(0, float("nan"), 1), (0, float("inf"), 1)])
def test_nonfinite_energies_rejected(energies):
    with pytest.raises(ValueError):
        summarize(rows(energies))


def test_duplicate_and_missing_images_rejected():
    values = rows()
    values.append(copy.deepcopy(values[0]))
    with pytest.raises(ValueError):
        summarize(values)
    with pytest.raises(ValueError):
        summarize(rows()[1:])


def test_endpoint_peak_is_flagged():
    assert summarize(rows((0, 0.5, 1)))[0]["interior_peak"] is False
