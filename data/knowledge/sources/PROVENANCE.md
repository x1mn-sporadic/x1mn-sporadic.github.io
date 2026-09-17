# Provenance of the copied source tables

| file | origin | commit | sha256 |
|---|---|---|---|
| `X1_N.csv` | `tables/X1_N.csv` of github.com/marin-varivoda/torsion_inf | ef78045be19f26a318a7b27a233aafb6da2675a4 (2026-05-27) | 2a93da522eb749bd8b19e2587ad7397de19b8961cd32e15dddb2871372947df5 |
| `X1_2_N.csv` | `tables/X1_2_N.csv` of github.com/marin-varivoda/torsion_inf | ef78045be19f26a318a7b27a233aafb6da2675a4 (2026-05-27) | d888b8c59cce033600036625e9d3f32533035b797e33149ab7fd614b1517b17e |
| `torsion_inf_tables_README.md` | `tables/README.md` of the same repository | same | — |

Column meaning (from the tables' README and the torsion_inf project):

* `g`, `an_r`, `index`: genus, analytic rank of J_1, index (LMFDB for X_1(N)).
* `gon_Q_lb`, `gon_Q_ub_DvH14`: lower and upper bounds for the Q-gonality; equal means the gonality is known
  (Derickx–van Hoeij 2014 for X_1(N), N ≤ 40; `note` column says how the lower bound was obtained
  otherwise: `DT` = CurveArith computation, `abramovich` = Abramovich's bound, `cover search`).
* `abramovich_lb` = (975/4096)/24 · index (Abramovich with Kim–Sarnak's λ₁ ≥ 975/4096).
* `f7`, `f8`, `f9`: X has a Q-rational function of degree 7, 8, 9.
* `p7`, `p8`, `p9`: X has infinitely many points of degree 7, 8, 9 (`???` = unknown).
  (The tables' README does not define the `f`/`p` columns; this reading was inferred from the data —
  it agrees with Derickx–van Hoeij 2014 for N ≤ 36 and with `gon_Q` — and should be confirmed by the
  torsion_inf authors before the degree 7–9 certificates are relied upon.)
  For X_1(N), N ≤ 36 (rank 0) these are Derickx–van Hoeij 2014, Theorem 3; the remaining entries are
  computations of the torsion_inf project.

The census pipeline (`pipeline/build.py`) reads only: `g`, `an_r`, `gon_Q_lb`, `gon_Q_ub_DvH14`, `p7`, `p8`, `p9`.
