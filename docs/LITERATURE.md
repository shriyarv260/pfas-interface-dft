# Literature evidence ledger

The source ledger was assembled on September 14, 2026. Research cited here predates the end of the supplied May–August 2026 project window, but this is not evidence that the project was actually executed during that window. Access dates and confidence of each retrieval are explicit in `references/sources.json`.

## Raghavan, Chaplin and Mehraeen, 2025

DOI: [10.1021/acs.jpcc.5c00542](https://doi.org/10.1021/acs.jpcc.5c00542). SI DOI: [10.1021/acs.jpcc.5c00542.s001](https://doi.org/10.1021/acs.jpcc.5c00542.s001).

The 45-page supporting PDF was downloaded from ACS Figshare and hashed. Section A2 (PDF page 3, printed page 2) reports a 0.96 eV decarboxylation barrier with 0.093 eV standard deviation for a PFOA radical surrounded by ten waters, **without a surface**. Table S2 (PDF page 6, printed page 5) provides five relaxed configuration energies. Those pages were checked visually against text extraction. The configuration identifiers in the surrounding prose and figure discussion are not assumed to map one-to-one onto table numbering; the CSV preserves Table S2 row numbers only.

The publisher repository abstract reports decreases of 0.34 eV in activation barrier and 1.05 eV in reaction energy with applied bias; these are stored as signed changes (biased minus unbiased). They are not absolute barriers. The exact original geometry/NEB inputs are not supplied here, and these values are not reproduced computations. Figures S6/S7 and frequency tables may guide a later reproduction, but do not substitute screenshots for coordinates or infer clean single-mode TS verification from table labels.

License for the downloaded SI: CC BY-NC 4.0, as declared by Figshare metadata. The original PDF is not bundled; the downloader retrieves the exact hash-verified file. Numerical CSV records are attributed and excluded from the software MIT license.

## Sharkas and Wong, 2025

DOI: [10.1021/acs.estlett.4c01130](https://doi.org/10.1021/acs.estlett.4c01130). Primary full-text record: [PMC11823447](https://pmc.ncbi.nlm.nih.gov/articles/PMC11823447/).

This study treats PFOA at Cu(111) with a constant-electrode-potential approach. Its indexed primary text describes bond cleavage under negative bias and distinguishes fixed-electron-count dynamics from the open-system calculation. This motivates explicit separation of the repository's fixed-charge runner from constant-potential claims. Publisher SI descriptions give vacuum-geometry settings (520 eV, 4×4×1, electronic 10−6 eV and forces 0.02 eV/Å); these are **not** copied into the QE starting config, which uses different units and a different workflow. The SI and author code were not downloaded in this build. No benchmark numbers were transcribed from its plots.

## McTaggart and Malardier-Jugroot, 2024

DOI: [10.1039/D3CP04973F](https://doi.org/10.1039/D3CP04973F). The publisher article connects electron capture, conformer changes, and fluoride release. It explicitly qualifies energetic interpretation of changes across charge states. Its ESI ZIP is linked by the publisher, but was not downloaded here. The repository uses it to motivate conformer sampling and charge-state care; no molecular coordinates or author scripts are claimed to come from that ZIP.

## Hydrated-electron study, 2022

DOI: [10.1021/acs.est.2c01469](https://doi.org/10.1021/acs.est.2c01469). The primary article treats PFOA/PFOS in explicit water with hydrated-electron dynamics and metadynamics. Its discussion differentiates an explicitly hydrated electron from merely adding excess charge. Its free-energy barriers are not interchangeable with the fixed-charge electronic NEB barriers produced here. No numeric dataset or source code from this paper is bundled.

## PFOS photo-electrochemical study, 2026

DOI: [10.1038/s41467-026-71263-9](https://doi.org/10.1038/s41467-026-71263-9). Indexed primary methods describe periodic DFT involving PFOS, Pd [111] and TiO2 [101], with desulfonation pathways. The data-availability statement identifies coordinates in Supplementary Data 1. This is a retrieval lead for future PFOS/interface work. The coordinate file was not downloaded or validated, so it does not support a numerical reproduction claim in this repository.

## Published software actually used

ASE 3.26.0 is imported as a dependency; its NEB, IDPP, FIRE, Espresso and Vibrations implementations do the corresponding numerical work. Source: [ASE GitLab](https://gitlab.com/ase/ase); scientific citation: [10.1088/1361-648X/aa680e](https://doi.org/10.1088/1361-648X/aa680e). The CI-NEB method citation is [10.1063/1.1329672](https://doi.org/10.1063/1.1329672). QE is an external electronic-structure engine: [official source](https://gitlab.com/QEF/q-e), [input specification](https://www.quantum-espresso.org/Doc/INPUT_PW.html). RDKit's [documented embedding tools](https://www.rdkit.org/docs/GettingStartedInPython.html) generate the starting conformers. The original wrapper code in this repository is not an author-provided PFAS reproduction package.
