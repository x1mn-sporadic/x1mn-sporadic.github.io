# Tables

This directory contains audit tables used to track the computations in this
repository.

## `X1_N.csv`

Columns `g`, `an_r`, and `index` were taken from
[beta.lmfdb.org](https://beta.lmfdb.org/).

The column `gon_Q_ub_DvH14` records the rational gonality upper bounds from:

> Maarten Derickx and Mark van Hoeij, "Gonality of the modular curve
> X1(N)", Journal of Algebra 417 (2014), 52--71.

The column `gon_Q_lb` records known lower bounds for the rational gonality.
When `gon_Q_lb = gon_Q_ub_DvH14`, the rational gonality is known exactly.

