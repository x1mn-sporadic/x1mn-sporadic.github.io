/* isolation_lib.m -- P^1-isolation of a verified point: is l(x) = dim L(x) = 1 on X_1(m,n)?

   Loaded by a job file (written by pipeline/verify.py) that first defines
     m, n           : integers (m <= 2 supported)
     fpoly          : defining polynomial (in x) of the residue field L of the point
     tb, tc         : Tate normal form b, c of (E, Q) as expressions in a (a root of fpoly)
     Px, Py         : coordinates of P on the Tate model (m = 2), expressions in a; "" for m = 1
     MdmagmaSpec    : path of mdmagma's v2/mdmagma.spec
     ModelsDir      : directory with the X1_2_n.txt model files (m = 2)
     LogFile, OutFile
     MaxPrimes      : optional, number of good primes to try (default 4)
   and writes a JSON object to OutFile:
     {ok, p1_isolated (true | "unknown"), primes: [q, ...], l_values: [l_q, ...], model, cputime}

   Method (as in sporadic_2x2n/code/direct_lib.m).  Let x be the closed point of degree d and
   q a prime with q not dividing n, q unramified in L, and (E, P, Q) having good reduction at
   every prime of L above q.  Then X_1(m,n) has good reduction at q, x extends to a horizontal
   divisor on the smooth model over Z_q, and its reduction is the degree-d divisor
       D_q = sum over the primes Q | q of L of the place of X/F_q of degree f(Q)
   given by the reduction of (E, P, Q) modulo Q.  Upper semicontinuity of h^0 gives
       dim L(D_q)  >=  dim L(x),
   so dim L(D_q) = 1 for ONE such q proves l(x) = 1, i.e. the point is P^1-isolated
   (Bourdon-Ejder-Liu-Odumodu-Viray).  If dim L(D_q) >= 2 for every prime tried, the answer is
   "unknown" (the point probably moves in a pencil, but a jump of h^0 cannot be excluded).

   The place above Q is identified on Sutherland's plane model (mdmagma) over F_q: the point
   (u, v) of the model over F_{q^f} with the right (b, c) values is found by a resultant, the
   places of the function field above u are constructed, and the one whose (b, c) values are
   Frobenius-conjugate to the reduced values is taken; the reduction is rejected unless it is
   unique.  Everything is computed in the algorithmic function field over F_q.
*/

T0 := Cputime();
procedure Log(s)
  Write(LogFile, Sprintf("[%o s] %o", RealField(6)!Cputime(T0), s));
end procedure;
procedure Emit(s)
  Write(OutFile, s : Overwrite := true);
end procedure;
procedure Fail(reason)
  Log("FAIL: " cat reason);
  Emit(Sprintf("{\"ok\": false, \"error\": \"%o\"}", reason));
end procedure;
if not assigned MaxPrimes then MaxPrimes := 4; end if;
if Type(MaxPrimes) eq MonStgElt then MaxPrimes := StringToInteger(MaxPrimes); end if;
if Type(m) eq MonStgElt then m := StringToInteger(m); end if;
if Type(n) eq MonStgElt then n := StringToInteger(n); end if;
if m ge 3 then Fail(Sprintf("isolation for m = %o not implemented", m)); quit; end if;

AttachSpec(MdmagmaSpec);
Qx<x> := PolynomialRing(Rationals());
L<a> := NumberField(Qx!(eval fpoly));
d := Degree(L);
OL := MaximalOrder(L);
b0 := L!(eval tb); c0 := L!(eval tc);
E0 := EllipticCurve([L | 1 - c0, -b0, -b0, 0, 0]);
Q0 := E0![0, 0];
P0 := E0!0;
if m gt 1 then P0 := E0![L | eval Px, eval Py]; end if;
Log(Sprintf("point: X_1(%o,%o), residue field degree %o", m, n, d));

// (b, c) in the coordinates of the model: Tate (b, c) for m = 1; for m = 2 the model is
// y^2 = x^3 + c x^2 + (1-b-c) b x with P = (0,0), Q = (b,b): move P0 to (0,0), scale Q0 to (b,b).
bv := b0; cv := c0;
if m eq 2 then
  a0 := aInvariants(E0);
  Es, fs := Transformation(E0, [0, a0[1]/2, a0[3]/2, 1]);       // complete the square: y^2 = cubic
  Ps := fs(P0);
  E1, f1 := Transformation(Es, [-Ps[1], 0, -Ps[2], 1]);         // P -> (0,0)
  ai := aInvariants(E1);
  error if ai[1] ne 0 or ai[3] ne 0 or ai[5] ne 0, "unexpected model after moving P to (0,0)";
  Q1 := f1(fs(Q0));
  u := Q1[2]/Q1[1];
  bv := Q1[1]/u^2; cv := ai[2]/u^2;
  error if ai[4]/u^4 ne (1 - bv - cv)*bv, "conversion to the (b,c) coordinates of the model failed";
end if;
Delta := Discriminant(E0);
model := m eq 1 select Sprintf("mdmagma MDX1(%o) (Sutherland's optimised model of X_1(%o))", n, n)
                 else Sprintf("mdmagma MDX11(2,%o) (Derickx-Sutherland model of X_1(2,%o))", n, n);

// genus over Q, to check that the reduction of the model is the reduction of the curve
gQ := Genus(CongruenceSubgroup([n, n, m]));

function ModelOverField(F)
  if m eq 1 then X := MDX1(n, F); else X := MDX11(2, n, F : equation_directory := ModelsDir); end if;
  C := Curve(X); FF := FunctionField(C);
  FA, toFA := AlgorithmicFunctionField(FF);
  bFF, cFF := Explode([FF!f : f in X`_coordinates]);
  bF := toFA(bFF); cF := toFA(cFF);
  Fpol := DefiningPolynomial(C);
  return X, C, FA, toFA, bF, cF, Fpol, [* bFF, cFF, toFA(FF.1) *];
end function;

// the place of X/F_q of degree f given by the reduced values (bbar, cbar) in k = F_{q^f}
function ReducedPlace(FA, bF, cF, Fpol, FF, k, bbar, cbar)
  Fq := ConstantField(FA); q := #Fq; f := Degree(k);
  Ruv<U, V> := PolynomialRing(k, 2);
  // the model is the projective closure of the affine plane curve in (u, v); dehomogenise
  aff := func<h | Rank(Parent(h)) eq 3 select Evaluate(h, [U, V, 1]) else Evaluate(h, [U, V])>;
  Fk := aff(Fpol);
  bnum := aff(Numerator(FF[1])); bden := aff(Denominator(FF[1]));
  cnum := aff(Numerator(FF[2])); cden := aff(Denominator(FF[2]));
  gb := bnum - bbar*bden;
  R := Resultant(Fk, gb, V);
  Ru := UnivariatePolynomial(R);
  if Ru eq 0 then return false, "resultant vanishes"; end if;
  pts := [];
  for r in Roots(Ru) do
    u0 := r[1];
    fu := UnivariatePolynomial(Evaluate(Fk, U, u0));
    gu := UnivariatePolynomial(Evaluate(gb, U, u0));
    if fu eq 0 then continue; end if;
    for rv in Roots(GCD(fu, gu)) do
      v0 := rv[1];
      if Evaluate(bden, [u0, v0]) eq 0 or Evaluate(cden, [u0, v0]) eq 0 then continue; end if;
      if Evaluate(cnum, [u0, v0]) ne cbar*Evaluate(cden, [u0, v0]) then continue; end if;
      Append(~pts, [u0, v0]);
    end for;
  end for;
  if #pts eq 0 then return false, "no point of the model with these (b, c) values (pole of a coordinate?)"; end if;
  cands := [];
  uF := FF[3];                                   // the first affine coordinate as an element of FA
  nplaces := 0;
  for pt in pts do
    t := MinimalPolynomial(pt[1], Fq);
    for pl in Zeros(Evaluate(t, uF)) do
      nplaces +:= 1;
      if Degree(pl) ne f then continue; end if;
      if pl in cands then continue; end if;
      kp, mkp := ResidueClassField(pl);
      eb := Evaluate(bF, pl); ec := Evaluate(cF, pl);
      if Type(eb) eq Infty or Type(ec) eq Infty then continue; end if;
      Embed(k, kp);
      okc := exists{j : j in [0..f-1] | kp!(bbar^(q^j)) eq kp!eb and kp!(cbar^(q^j)) eq kp!ec};
      if okc then Append(~cands, pl); end if;
    end for;
  end for;
  if #cands ne 1 then return false, Sprintf("%o candidate places (%o model points, %o places above them)", #cands, #pts, nplaces); end if;
  return true, cands[1];
end function;

primes_used := []; lvals := []; isolated := false;
q := 2; tried := 0;
while tried lt MaxPrimes and q lt 200 do
  q := NextPrime(q);
  if n mod q eq 0 or Discriminant(OL) mod q eq 0 then continue; end if;
  dec := Decomposition(OL, q);
  bad := false;
  for pr in dec do
    Qi := pr[1];
    if Valuation(bv, Qi) lt 0 or Valuation(cv, Qi) lt 0 or Valuation(Delta, Qi) ne 0 then bad := true; break; end if;
    if m eq 2 and (Valuation(P0[1], Qi) lt 0 or Valuation(P0[2], Qi) lt 0) then bad := true; break; end if;
  end for;
  if bad then Log(Sprintf("q = %o: bad reduction, skipped", q)); continue; end if;
  tried +:= 1;
  ok := true;
  X := 0; C := 0; FA := 0; toFA := 0; bF := 0; cF := 0; Fpol := 0; FFs := 0;
  try
    X, C, FA, toFA, bF, cF, Fpol, FFs := ModelOverField(GF(q));
    if Genus(FA) ne gQ then
      Log(Sprintf("q = %o: model has genus %o != %o, skipped", q, Genus(FA), gQ)); ok := false;
    end if;
  catch e
    Log(Sprintf("q = %o: model failed (%o), skipped", q, e`Object)); ok := false;
  end try;
  if not ok then continue; end if;
  D := DivisorGroup(FA)!0;
  for pr in dec do
    Qi := pr[1];
    k, mk := ResidueClassField(Qi);
    okp, pl := ReducedPlace(FA, bF, cF, Fpol, FFs, k, mk(bv), mk(cv));
    if not okp then Log(Sprintf("q = %o: %o, skipped", q, pl)); ok := false; break; end if;
    D +:= 1*pl;
  end for;
  if not ok then continue; end if;
  error if Degree(D) ne d, "reduced divisor has the wrong degree";
  l := Dimension(RiemannRochSpace(D));
  Append(~primes_used, q); Append(~lvals, l);
  Log(Sprintf("q = %o: D_q = %o places of degrees %o, dim L(D_q) = %o (%o s)", q, #Support(D), [Degree(p) : p in Support(D)], l, RealField(6)!Cputime(T0)));
  if l eq 1 then isolated := true; break; end if;
end while;

if #primes_used eq 0 then Fail("no usable prime found"); quit; end if;
Emit(Sprintf("{\"ok\": true, \"p1_isolated\": %o, \"primes\": %o, \"l_values\": %o, \"model\": \"%o\", \"cputime\": \"%o\"}",
     isolated select "true" else "\"unknown\"", primes_used, lvals, model, RealField(6)!Cputime(T0)));
Log("ISOLATION_DONE");
