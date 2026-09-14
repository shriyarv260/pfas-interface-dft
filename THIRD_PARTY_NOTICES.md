# Third-party notices

The MIT license applies only to original software and original documentation/fixtures in this repository. It does not relicense literature data, papers, third-party dependencies, pseudopotentials or engine outputs obtained elsewhere.

| Item | Origin | License / treatment |
|---|---|---|
| ASE 3.26.0 | https://gitlab.com/ase/ase | LGPL-2.1-or-later; installed dependency, not vendored |
| Quantum ESPRESSO | https://gitlab.com/QEF/q-e | GPL-2.0; external engine, not bundled |
| RDKit | https://github.com/rdkit/rdkit | BSD-3-Clause; optional conformer-generation dependency |
| NumPy, SciPy | Official Python distributions | BSD-style; installed scientific dependencies |
| Matplotlib | Official Python distribution | Matplotlib license; installed plotting dependency |
| Raghavan et al. SI-derived numerical records | DOI 10.1021/acs.jpcc.5c00542.s001 | CC BY-NC 4.0 per Figshare metadata; attribution below |

Attribution for `data/literature/ti4o7_table_s2.csv` and the SI-derived reference entry: Srishyam Raghavan, Brian P. Chaplin, Shafigh Mehraeen (2025), supporting information to DOI 10.1021/acs.jpcc.5c00542. Modifications: selected numbers transcribed to CSV/JSON with labels and provenance; source layout not preserved. License: https://creativecommons.org/licenses/by-nc/4.0/. The benchmark tolerances are original project policy, not source data.

Other paper abstracts/articles are linked and summarized with attribution, not redistributed. No PFAS author scripts were recovered, copied or relicensed. The repository calls ASE APIs using original orchestration code. Dependencies retain their own notices; consult the installed distributions for complete license texts.

Do not commit VASP POTCAR files or other restricted pseudopotentials. Select externally sourced QE pseudopotentials under compatible terms, record checksums and preserve their attribution/license.
