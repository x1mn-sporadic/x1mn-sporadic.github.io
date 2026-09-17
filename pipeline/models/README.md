# Models of X₁(m,n) used by the isolation check

`X1_m_n/X1_<m>_<n>.txt` — plane models of X₁(m,n) (Derickx–Sutherland, *Torsion subgroups of elliptic
curves over quintic and sextic number fields*, https://math.mit.edu/~drew/X1mn.html), in the file format of
mdmagma's `models_X1_m_n/` directory, with wrapped lines joined so that mdmagma's reader accepts every
file (it chokes on the original `X1_2_16.txt`). Each file gives the equation `X` in `u, v` and the
elliptic curve `E` with its points `P` (order m) and `Q` (order n) as functions on the model. For m = 2
mdmagma's coordinates are (b, c) with `E: y² = x³ + c x² + (1−b−c) b x`, `P = (0,0)`, `Q = (b,b)`.

Models of X₁(N) (m = 1) are read by mdmagma from its own `models_X1_n/` directory (Sutherland–van Hoeij
optimised equations). mdmagma itself is the git submodule `pipeline/external/mdmagma`
(github.com/koffie/mdmagma, pinned).
