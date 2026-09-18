/* isolation_lib.m -- P^1-isolation of a verified point: is l(x) = dim L(x) = 1 on X_1(m,n)?

   Loaded by a job file (written by pipeline/verify.py) that first defines
     m, n           : integers
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

   The place above Q is identified on Sutherland's plane model (mdmagma) over F_q through the
   Tate data of the level structure -- (b, c) of the Tate normal form of (E, Q), and x(P), y(P) on
   it for m >= 2 -- which determine the point of X_1(m,n): the same data are computed as functions
   on the model (from the model's E, P, Q), the places above the low-degree factors of the norm of
   minpoly(b-bar)(b) are constructed (cheap over F_q), and the one whose values are Frobenius-
   conjugate to the reduced values is taken; the reduction is rejected unless it is unique.
   For m >= 3 the curve lives over Q(zeta_m); the model over F_q (q = 1 mod m) built with a
   primitive root z is its reduction at the prime of Q(zeta_m) where zeta_m = z (up to the
   model's convention for the Weil pairing), so only the primes Q of L above that prime match a
   place; the matched places must add up to degree d/phi(m), the degree of x over Q(zeta_m).
   Everything is computed in the algorithmic function field over F_q.
*/

T0 := Cputime();
procedure Log(s)
  Write(LogFile, Sprintf("[%o s] %o", RealField(6)!Cputime(T0), s));
end procedure;
if not assigned MaxPrimes then MaxPrimes := 4; end if;
if Type(MaxPrimes) eq MonStgElt then MaxPrimes := StringToInteger(MaxPrimes); end if;
AttachSpec(MdmagmaSpec);

// Tate normal form of (E, Q), Q of order >= 4 (Magma: x' = u^2 x + r, y' = u^3 y + s u^2 x + t).
function TateNormalForm(E, Q)
  E1, f1 := Transformation(E, [-Q[1], 0, -Q[2], 1]);
  a := aInvariants(E1);
  error if a[5] ne 0 or a[3] eq 0, "Tate normal form: bad point";
  E2, f2 := Transformation(E1, [0, -a[4]/a[3], 0, 1]);
  a := aInvariants(E2);
  error if a[2] eq 0, "Tate normal form: Q has order 3";
  E3, f3 := Transformation(E2, [0, 0, 0, a[2]/a[3]]);
  a := aInvariants(E3);
  return E3, -a[2], 1 - a[1], f1*f2*f3;
end function;

// the model file's q(u,v), t(u,v) for m = 2 (mdmagma keeps only b, c); used to invert (b, c) -> (u, v)
function QTLines(m, n)
  if m ne 2 then return []; end if;
  lines := [];
  for l in Split(Read(Sprintf("%o/X1_2_%o.txt", ModelsDir, n)), "\n") do
    if #l ge 4 and (l[1..4] eq "q :=" or l[1..4] eq "t :=") then Append(~lines, Split(Split(l, ";")[1], "=")[2]); end if;
  end for;
  error if #lines ne 2, "q and t not found in the model file";
  return lines;
end function;

// the model of X_1(m,n) over F (z: primitive m-th root of unity in F for m >= 3) and the comparison
// functions: mdmagma's (b, c) for m <= 2, the Tate data (b, c, x(P), y(P)) of the model's (E, P, Q) for m >= 3
function ModelOverField(m, n, F, z)
  if m eq 1 then X := MDX1(n, F);
  elif m eq 2 then X := MDX11(2, n, F : equation_directory := ModelsDir);
  else X := MDX11(m, n, F : equation_directory := ModelsDir, zeta_M := z); end if;
  C := Curve(X); FF := FunctionField(C);
  FA, toFA := AlgorithmicFunctionField(FF);
  if m le 2 then
    FFs := [FF!f : f in X`_coordinates];
  else
    Em := EllipticCurve([FF!a : a in X`_E]);
    Pm := Em![FF!x : x in X`_P]; Qm := Em![FF!x : x in X`_Q];
    Et, bF, cF, iso := TateNormalForm(Em, Qm);
    Pt := iso(Pm);
    FFs := [bF, cF, Pt[1], Pt[2]];
  end if;
  Fs := [toFA(f) : f in FFs];
  return FA, Fs, FFs, toFA(FF.1), DefiningPolynomial(C);
end function;

// the place of X/F_q of degree f where the functions Fs take values Frobenius-conjugate to vals
// (in k = F_{q^f}).  Candidate points (u0, v0) of the plane model over k: for m = 1 by inverting
// Sutherland's r, s (b = r s (r-1), c = s (r-1)); for m = 2 by inverting mdmagma's (b, c) -> (q, t)
// and the model file's q(u,v), t(u,v); for m >= 3 by a resultant with b(u,v).  The places above
// u = u0 are the zeros of t(u), t the minimal polynomial of u0 over F_q.
function ReducedPlace(m, FA, Fs, FFs, uF, Fpol, qt_lines, k, vals)
  Fq := ConstantField(FA); q := #Fq; f := Degree(k);
  Ruv<U, V> := PolynomialRing(k, 2);
  aff := func<h | Rank(Parent(h)) eq 3 select Evaluate(h, [U, V, 1]) else Evaluate(h, [U, V])>;
  Fk := aff(Fpol);
  pts := [];
  if m eq 1 then
    bb := vals[1]; cc := vals[2];
    if cc eq 0 then return false, "c = 0 at this prime"; end if;
    rb := bb/cc;
    if rb eq 1 then return false, "r = 1 at this prime"; end if;
    sb := cc/(rb - 1);
    Rk<Xk> := PolynomialRing(k); Fr := FieldOfFractions(Rk);
    Yk := 1/((sb - 1)*Fr!Xk + 1);
    eqr := Numerator((Xk^2*Yk - Xk*Yk + Yk - 1) - rb*Xk*(Xk*Yk - 1));
    for r in Roots(eqr) do
      x0 := r[1];
      if (sb - 1)*x0 + 1 eq 0 or x0 eq 0 then continue; end if;
      y0 := 1/((sb - 1)*x0 + 1);
      if Evaluate(Fk, [x0, y0]) eq 0 then Append(~pts, [x0, y0]); end if;
    end for;
  elif m eq 2 then
    bb := vals[1]; cc := vals[2];
    if cc eq 1 then return false, "c = 1 at this prime"; end if;
    tb := 2*bb/(1 - cc) - 1;
    if tb eq 0 then return false, "t = 0 at this prime"; end if;
    qb := ((1 - cc)*tb^2 - 2)/(2*tb);
    Kuv := FieldOfFractions(Ruv); u := Kuv!U; v := Kuv!V;
    qf := eval qt_lines[1]; tf := eval qt_lines[2];
    g1 := Numerator(qf - qb); g2 := Numerator(tf - tb);
    Ru := UnivariatePolynomial(Resultant(Ruv!g1, Ruv!g2, V));
    if Ru eq 0 then return false, "resultant vanishes"; end if;
    for r in Roots(Ru) do
      u0 := r[1];
      h1 := UnivariatePolynomial(Evaluate(Ruv!g1, U, u0)); h2 := UnivariatePolynomial(Evaluate(Ruv!g2, U, u0));
      hh := GCD(h1, h2);
      if hh eq 0 then hh := h1 eq 0 select h2 else h1; end if;
      for rv in Roots(hh) do
        if Evaluate(Fk, [u0, rv[1]]) eq 0 then Append(~pts, [u0, rv[1]]); end if;
      end for;
    end for;
  else
    bnum := aff(Numerator(FFs[1])); bden := aff(Denominator(FFs[1]));
    gb := bnum - vals[1]*bden;
    Ru := UnivariatePolynomial(Resultant(Fk, gb, V));
    if Ru eq 0 then return false, "resultant vanishes"; end if;
    for r in Roots(Ru) do
      u0 := r[1];
      fu := UnivariatePolynomial(Evaluate(Fk, U, u0));
      gu := UnivariatePolynomial(Evaluate(gb, U, u0));
      if fu eq 0 then continue; end if;
      for rv in Roots(GCD(fu, gu)) do Append(~pts, [u0, rv[1]]); end for;
    end for;
  end if;
  if #pts eq 0 then return false, "no point of the model with these values (pole of a coordinate?)"; end if;
  cands := [];
  for pt in pts do
    t := MinimalPolynomial(pt[1], Fq);
    for pl in Zeros(Evaluate(t, uF)) do
      if Degree(pl) ne f or pl in cands then continue; end if;
      ev := [Evaluate(g, pl) : g in Fs];
      if exists{e : e in ev | Type(e) eq Infty} then continue; end if;
      kp := ResidueClassField(pl);
      Embed(k, kp);
      if exists{j : j in [0..f-1] | forall{i : i in [1..#Fs] | kp!(vals[i]^(q^j)) eq kp!ev[i]}} then Append(~cands, pl); end if;
    end for;
  end for;
  if #cands ne 1 then return false, Sprintf("%o candidate places", #cands); end if;
  return true, cands[1];
end function;

/* IsolationCheck: the whole computation for one point.  `cache` (associative array, keyed by
   <q, z>) holds the models already built for this curve, so that a batch of points on the same
   curve pays the integral closure of the function field once per prime.  Returns the JSON string. */
procedure IsolationCheck(m, n, fpoly, tb, tc, Px, Py, MaxPrimes, ~cache, ~json)
  Qx<x> := PolynomialRing(Rationals());
  fL := Qx!(eval fpoly);
  L<a> := NumberField(fL);
  d := Degree(L);
  discf := Discriminant(fL);
  b0 := L!(eval tb); c0 := L!(eval tc);
  E0 := EllipticCurve([L | 1 - c0, -b0, -b0, 0, 0]);
  Q0 := E0![0, 0];
  P0 := E0!0;
  if m gt 1 then P0 := E0![L | eval Px, eval Py]; end if;
  phi_m := EulerPhi(m);
  Log(Sprintf("point: X_1(%o,%o), residue field degree %o", m, n, d));
  vals0 := [b0, c0];
  if m eq 2 then
    a0 := aInvariants(E0);
    Es, fs := Transformation(E0, [0, a0[1]/2, a0[3]/2, 1]);
    Ps := fs(P0);
    E1, f1 := Transformation(Es, [-Ps[1], 0, -Ps[2], 1]);
    ai := aInvariants(E1);
    error if ai[1] ne 0 or ai[3] ne 0 or ai[5] ne 0, "unexpected model after moving P to (0,0)";
    Q1 := f1(fs(Q0));
    u := Q1[2]/Q1[1];
    bv := Q1[1]/u^2; cv := ai[2]/u^2;
    error if ai[4]/u^4 ne (1 - bv - cv)*bv, "conversion to the (b,c) coordinates of the model failed";
    vals0 := [bv, cv];
  elif m ge 3 then
    vals0 := [b0, c0, P0[1], P0[2]];
    zeta := WeilPairing(P0, (n div m)*Q0, m);
    error if zeta^m ne 1 or exists{e : e in Divisors(m) | e lt m and zeta^e eq 1}, "P, Q do not generate Z/m x Z/n";
  end if;
  Delta := Discriminant(E0);
  model := m eq 1 select Sprintf("mdmagma MDX1(%o) (Sutherland's optimised model of X_1(%o))", n, n)
                   else Sprintf("mdmagma MDX11(%o,%o) (Derickx-Sutherland model of X_1(%o,%o))", m, n, m, n);
  gQ := Genus(CongruenceSubgroup([n, n, m]));
  qt_lines := QTLines(m, n);
  // reduction modulo the primes above q read off f mod q (q not dividing disc f: unramified, Z[a] q-maximal)
  reduce := function(z, q, r, k)
    cs := Eltseq(z);
    if exists{c : c in cs | Denominator(c) mod q eq 0} then return false, k!0; end if;
    return true, &+[ (k!(GF(q)!cs[i])) * r^(i-1) : i in [1..#cs] ];
  end function;
  primes_used := []; lvals := []; isolated := false;
  q := 2; tried := 0;
  while tried lt MaxPrimes and q lt 500 do
    q := NextPrime(q);
    if n mod q eq 0 or Numerator(discf) mod q eq 0 or Denominator(discf) mod q eq 0 or (m ge 3 and q mod m ne 1) then continue; end if;
    if exists{c : c in Coefficients(fL) | Denominator(c) mod q eq 0} or Integers()!Numerator(LeadingCoefficient(fL)) mod q eq 0 then continue; end if;
    fq := PolynomialRing(GF(q))![GF(q)!c : c in Coefficients(fL)];
    dec := [* *];     // one entry <k, r, values> per prime above q: residue field, root, reduced values
    bad := false;
    for t in Factorization(fq) do
      if Degree(t[1]) eq 1 then k := GF(q); r := -Coefficient(t[1], 0)/Coefficient(t[1], 1);
      else k := ext< GF(q) | t[1] >; r := k.1; end if;
      okr, Dq := reduce(Delta, q, r, k);
      if not okr or Dq eq 0 then bad := true; break; end if;
      vq := [];
      for v in vals0 do
        okr, vv := reduce(v, q, r, k); if not okr then bad := true; break; end if; Append(~vq, vv);
      end for;
      if bad then break; end if;
      Append(~dec, <k, r, vq>);
    end for;
    if bad then Log(Sprintf("q = %o: bad reduction, skipped", q)); continue; end if;
    tried +:= 1;
    z := m ge 3 select Rep([r[1] : r in Roots(CyclotomicPolynomial(m), GF(q))]) else 0;
    key := <q, z>;
    ok := true;
    if not IsDefined(cache, key) then
      try
        FA, Fs, FFs, uF, Fpol := ModelOverField(m, n, GF(q), z);
        Log(Sprintf("q = %o: model built (%o s); computing the maximal orders of its function field (genus check)", q, RealField(6)!Cputime(T0)));
        g := Genus(FA);
        cache[key] := <FA, Fs, FFs, uF, Fpol, g eq gQ>;
        Log(Sprintf("q = %o: genus %o (expected %o), %o s", q, g, gQ, RealField(6)!Cputime(T0)));
      catch e
        Log(Sprintf("q = %o: model failed (%o), skipped", q, e`Object)); ok := false;
      end try;
    end if;
    if not ok then continue; end if;
    FA, Fs, FFs, uF, Fpol, gok := Explode(cache[key]);
    if not gok then Log(Sprintf("q = %o: wrong genus, skipped", q)); continue; end if;
    D := DivisorGroup(FA)!0;
    nfound := 0;
    for pr in dec do
      k := pr[1];
      okp, pl := ReducedPlace(m, FA, Fs, FFs, uF, Fpol, qt_lines, k, pr[3]);
      if okp then D +:= 1*pl; nfound +:= 1;
      elif m le 2 then Log(Sprintf("q = %o: %o, skipped", q, pl)); ok := false; break; end if;
    end for;
    if not ok then continue; end if;
    if Degree(D) ne d div phi_m then
      Log(Sprintf("q = %o: matched %o of %o primes, reduced divisor has degree %o instead of %o, skipped", q, nfound, #dec, Degree(D), d div phi_m));
      continue;
    end if;
    l := Dimension(RiemannRochSpace(D));
    Append(~primes_used, q); Append(~lvals, l);
    Log(Sprintf("q = %o: D_q = %o places of degrees %o, dim L(D_q) = %o (%o s)", q, #Support(D), [Degree(p) : p in Support(D)], l, RealField(6)!Cputime(T0)));
    if l eq 1 then isolated := true; break; end if;
  end while;
  if #primes_used eq 0 then
    json := "{\"ok\": false, \"error\": \"no usable prime found\"}";
  else
    json := Sprintf("{\"ok\": true, \"p1_isolated\": %o, \"primes\": %o, \"l_values\": %o, \"model\": \"%o\", \"cputime\": \"%o\"}",
        isolated select "true" else "\"unknown\"", primes_used, lvals, model, RealField(6)!Cputime(T0));
  end if;
end procedure;

// ---------------------------------------------------------------- single-point driver
if assigned fpoly then
  if Type(m) eq MonStgElt then m := StringToInteger(m); end if;
  if Type(n) eq MonStgElt then n := StringToInteger(n); end if;
  cache := AssociativeArray();
  json := "";
  try
    IsolationCheck(m, n, fpoly, tb, tc, Px, Py, MaxPrimes, ~cache, ~json);
  catch e
    msg := Sprint(e`Object);
    msg := &cat[c eq "\n" select " " else (c eq "\"" select "'" else c) : c in Eltseq(msg)];
    json := Sprintf("{\"ok\": false, \"error\": \"%o\"}", msg);
    Log("FAIL: " cat msg);
  end try;
  Write(OutFile, json : Overwrite := true);
  Log("ISOLATION_DONE");
end if;
