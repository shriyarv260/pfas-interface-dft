# What 95% can and cannot mean

The user's requested 95% accuracy is treated as a target to define and test, never as an output to manufacture. Software test pass rate, DFT numerical reproduction, agreement with experiment, and percent PFAS defluorination are four different quantities.

The versioned policy in `configs/benchmark_policy.json` proposes at least 95% of preregistered energy-difference cases within declared absolute eV tolerances and at least 20 independent cases. The initial ±0.10 eV tolerances are provisional repository choices, not taken from the papers. A relative percentage error is unstable near zero and depends badly on arbitrary total-energy offsets.

Current state: three published reference quantities from one study, two independence groups, zero independently calculated predictions. The no-surface 0.96 eV barrier must not be paired with a surface calculation. The two applied-bias deltas are correlated. Table S2 total energies are provenance data, excluded from the accuracy score. This repository cannot currently support the requested accuracy claim.

## Benchmark procedure

1. Preregister molecules, surfaces, reactions, reference structures, solvation, charge/potential, functional, pseudopotentials, tolerances, exclusions and independence groups before running predictions.
2. Reproduce the same observable and conditions; document any author input files obtained. Missing coordinates or method details make a case pending, not automatically comparable.
3. Keep convergence/tuning cases distinct from held-out evaluation cases. Do not tune tolerances to the computed errors.
4. Archive raw outputs, method/input/pseudopotential hashes, convergence and transition-state evidence. The prediction record must point to a result artifact hash.
5. Submit computed predictions with matching IDs/quantity/condition, `status: computed`, and `converged: true`. The example JSON is a schema illustration; never change its status without evidence.
6. Run `pfas benchmark`. Missing/ineligible cases remain in the denominator. Duplicate/unknown IDs and nonfinite values fail. Coverage must be complete before `target_met` is possible.
7. Report n, coverage, independent groups, MAE, RMSE, tolerances, pass fraction, exclusions and evidence. Have a scientific reviewer verify independence and condition matching; metadata strings cannot prove either.

The Wilson interval is a descriptive 95% binomial interval only. It is not evidence of 95% physical accuracy; correlation invalidates its simple interpretation. Passing 19/20 cases meets an empirical 95% target but does not put the population success rate above 95% with 95% confidence. The policy does not claim that stronger guarantee.

The benchmark reads artifact hashes but cannot verify arbitrary external files from a JSON value alone. Review and archive the corresponding raw artifacts. A converged NEB still needs a mode check and chemistry review.

## Quality assurance levels

- Executed locally: automated software tests, analytic force finite differences, analytic barrier recovery, generated formula checks, interface/path preparation, QE input writing, and intentional benchmark failure for no data.
- Prepared for external execution: endpoint DFT, production PFAS CI-NEB and finite-difference vibrations with Quantum ESPRESSO.
- Not executed: production PFAS electronic structure, constant-potential dynamics, independent literature reproduction, defect ranking, degradation-efficiency prediction.

The exact verification commands and results for this delivery are recorded in `docs/VERIFICATION.md`.
