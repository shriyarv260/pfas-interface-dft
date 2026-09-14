# Delivery verification — September 14, 2026

Local environment: macOS arm64, Python 3.12.14, ASE 3.26.0, NumPy 2.2.6, SciPy 1.15.3, Matplotlib 3.10.3. Exact installed dependency versions are recorded in `requirements-lock.txt`. Python 3.11 and Linux are configured in CI but have not been run locally or remotely for this delivery.

| Check | Observed outcome |
|---|---|
| Editable package build/install | Passed using installed setuptools and `pip install --no-build-isolation --no-deps -e .` |
| `pip check` | No broken requirements |
| `ruff check src tests scripts` | Passed |
| `ruff format --check src tests scripts` | Passed |
| `pytest -q` | **35 passed**; 14 upstream Matplotlib/pyparsing deprecation warnings |
| `pfas demo --output examples/demo_result` | Converged analytical CI-NEB; sampled barrier 1.000000725353 eV versus exact 1.0 eV |
| PFOA/Cu(111) preparation | Created `examples/pfoa_cu_starting_guess/initial.traj` and provenance |
| QE input serialization | Created `examples/qe_input/pw.in`; pseudopotentials explicitly unverified |
| Benchmark with bundled references and empty predictions | `not_validated`; expected exit code 2 |
| Audited SI verification | Downloader verified the original PDF against recorded SHA-256 |
| Local Markdown links / JSON records | Resolved / parsed successfully |
| Demo plot | Visually inspected; labels explicitly distinguish synthetic output |

Tests include analytical force finite differences, known barrier recovery, force-convergence guards, atom/cell/constraint conservation, identical-endpoint rejection, molecule formulas and hashes, invalid QE input rejection, and protection against synthetic/missing/incompatible benchmark predictions. Production-run orchestration is also exercised with the analytical calculator substituted for QE; this does not test QE electronic structure.

The initial system Python/Git launchers were unavailable, so a bundled Python/Git runtime was used. An initial editable-install attempt lacked a build backend; installation succeeded after adding setuptools/wheel to the isolated work environment. An initial latest-NumPy environment emitted ASE deprecation warnings; the tested numerical versions above avoid those warnings. Remaining pyparsing warnings are upstream compatibility notices, not failed tests. On this sandbox, some ASE imports also attempted a Matplotlib cache outside the writable workspace; Matplotlib fell back to a temporary cache. Set `MPLCONFIGDIR` to a writable directory in similarly restricted environments.

**No production PFAS DFT, experimental validation, constant-potential calculation, catalyst ranking, or 95% scientific accuracy result was produced.** The external Quantum ESPRESSO binary, pseudopotentials, reviewed reaction endpoints and HPC execution remain prerequisites for such results.
