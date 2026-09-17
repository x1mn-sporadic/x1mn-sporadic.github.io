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
AttachSpec(MdmagmaSpec);
phi_m := EulerPhi(m);
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

// Our point in the coordinates the model will be compared with:
//   m = 1: the Tate (b, c)  (the model IS the Tate normal form);
//   m = 2: mdmagma's (b, c) with E: y^2 = x^3 + c x^2 + (1-b-c) b x, P = (0,0), Q = (b,b);
//   m >= 3: the Tate data (b, c, x(P), y(P)) of (E, P, Q).
vals0 := [b0, c0];
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
  vals0 := [bv, cv];
elif m ge 3 then
  vals0 := [b0, c0, P0[1], P0[2]];
  zeta := WeilPairing(P0, (n div m)*Q0, m);
  error if zeta^m ne 1 or exists{e : e in Divisors(m) | e lt m and zeta^e eq 1}, "P, Q do not generate Z/m x Z/n";
end if;
Delta := Discriminant(E0);
model := m eq 1 select Sprintf("mdmagma MDX1(%o) (Sutherland's optimised model of X_1(%o))", n, n)
                 else Sprintf("mdmagma MDX11(%o,%o) (Derickx-Sutherland model of X_1(%o,%o))", m, n, m, n);

// genus over Q, to check that the reduction of the model is the reduction of the curve
gQ := Genus(CongruenceSubgroup([n, n, m]));

// the model over F_q (z: primitive m-th root of unity in F_q, m >= 3) and the comparison functions
function ModelOverField(F, z)
  if m eq 1 then X := MDX1(n, F);
  elif m eq 2 then X := MDX11(2, n, F : equation_directory := ModelsDir);
  else X := MDX11(m, n, F : equation_directory := ModelsDir, zeta_M := z); end if;
  C := Curve(X); FF := FunctionField(C);
  FA, toFA := AlgorithmicFunctionField(FF);
  if m le 2 then
    Fs := [toFA(FF!f) : f in X`_coordinates];
  else
    Em := EllipticCurve([toFA(FF!a) : a in X`_E]);
    Pm := Em![toFA(FF!x) : x in X`_P]; Qm := Em![toFA(FF!x) : x in X`_Q];
    Et, bF, cF, iso := TateNormalForm(Em, Qm);
    Pt := iso(Pm);
    Fs := [bF, cF, Pt[1], Pt[2]];
  end if;
  return FA, Fs;
end function;

// the place of X/F_q of degree f where the functions Fs take values Frobenius-conjugate to vals (in k = F_{q^f})
function ReducedPlace(FA, Fs, k, vals)
  Fq := ConstantField(FA); q := #Fq; f := Degree(k);
  mb := MinimalPolynomial(vals[1], Fq);
  h := Evaluate(mb, Fs[1]);
  if h eq 0 then return false, "b is constant on the model"; end if;
  nm := Norm(h);
  cands := [];
  for t in Factorization(Numerator(nm)) do
    if Degree(t[1]) gt f then continue; end if;
    for pl in Zeros(FA!t[1]) do
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

primes_used := []; lvals := []; isolated := false;
q := 2; tried := 0;
while tried lt MaxPrimes and q lt 500 do
  q := NextPrime(q);
  if n mod q eq 0 or Discriminant(OL) mod q eq 0 or (m ge 3 and q mod m ne 1) then continue; end if;
  dec := Decomposition(OL, q);
  bad := false;
  for pr in dec do
    Qi := pr[1];
    if exists{v : v in vals0 | Valuation(v, Qi) lt 0} or Valuation(Delta, Qi) ne 0 then bad := true; break; end if;
  end for;
  if bad then Log(Sprintf("q = %o: bad reduction, skipped", q)); continue; end if;
  tried +:= 1;
  ok := true;
  FA := 0; Fs := [];
  z := m ge 3 select Rep([r[1] : r in Roots(CyclotomicPolynomial(m), GF(q))]) else 0;
  try
    FA, Fs := ModelOverField(GF(q), z);
    if Genus(FA) ne gQ then
      Log(Sprintf("q = %o: model has genus %o != %o, skipped", q, Genus(FA), gQ)); ok := false;
    end if;
  catch e
    Log(Sprintf("q = %o: model failed (%o), skipped", q, e`Object)); ok := false;
  end try;
  if not ok then continue; end if;
  D := DivisorGroup(FA)!0;
  nfound := 0;
  for pr in dec do
    Qi := pr[1];
    k, mk := ResidueClassField(Qi);
    okp, pl := ReducedPlace(FA, Fs, k, [mk(v) : v in vals0]);
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

if #primes_used eq 0 then Fail("no usable prime found"); quit; end if;
Emit(Sprintf("{\"ok\": true, \"p1_isolated\": %o, \"primes\": %o, \"l_values\": %o, \"model\": \"%o\", \"cputime\": \"%o\"}",
     isolated select "true" else "\"unknown\"", primes_used, lvals, model, RealField(6)!Cputime(T0)));
Log("ISOLATION_DONE");
