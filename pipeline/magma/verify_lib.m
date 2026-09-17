/* verify_lib.m -- Magma checks for a submitted point on X_1(m,n).

   Loaded by a job file (written by pipeline/verify.py) that first defines:

     m, n            : integers, m | n, n >= 4
     fpoly           : string, defining polynomial of K in x (rational coefficients)
     mode            : "ainvs" | "tate" | "vanhoeij"
     ainvs           : [5 strings in a]                 (mode "ainvs")
     tb, tc          : strings in a                     (mode "tate":  E: y^2 + (1-c)xy - by = x^3 - bx^2, Q = (0,0))
     eqxy            : string in x, y                   (mode "vanhoeij": fpoly is eqx; residue field Q(x0,y0))
     Pxy, Qxy        : [2 strings in a] or []           (optional coordinates of P, Q on the given model)
     LogFile, OutFile: strings (paths); LogFile gets progress lines, OutFile gets one JSON object
     SkipFullTorsion : boolean (optional, default false)
     MemGB           : integer (optional)

   All strings have been whitelisted by verify.py (digits, a/x/y, + - * / ^ ( ) and spaces only)
   before they reach `eval` here.

   Everything the certificate later relies on is recomputed here from the submitted data:
     * K is a number field of the stated degree, E is an elliptic curve over K;
     * Q has exact order n, P has exact order m and <P,Q> = Z/m x Z/n;
     * |E(K)_tors| divides the gcd of #E(F_p) over good unramified degree-1 primes p (p not above 2),
       and the full torsion subgroup when it can be computed;
     * the Tate normal form (b,c) of (E,Q) and the residue field L = Q(b,c,x(P),y(P)) of the
       point of X_1(m,n): its degree is the degree of the point;
     * j, its minimal polynomial, [Q(j):Q], CM or not.
*/

if not assigned SkipFullTorsion then SkipFullTorsion := false; end if;
if not assigned ainvs then ainvs := []; end if;
if not assigned tb then tb := ""; end if;
if not assigned tc then tc := ""; end if;
if not assigned eqxy then eqxy := ""; end if;
if not assigned Pxy then Pxy := []; end if;
if not assigned Qxy then Qxy := []; end if;
if assigned MemGB then
  if Type(MemGB) eq MonStgElt then MemGB := StringToInteger(MemGB); end if;
  SetMemoryLimit(MemGB * 10^9);
end if;

T0 := Cputime();

procedure Log(s)
  Write(LogFile, Sprintf("[%o s] %o", RealField(6)!Cputime(T0), s));
end procedure;

// ---------------------------------------------------------------- tiny JSON writer
function JStr(s)
  t := "";
  for i in [1..#s] do
    c := s[i];
    if c eq "\"" then t cat:= "\\\"";
    elif c eq "\\" then t cat:= "\\\\";
    elif c eq "\n" then t cat:= "\\n";
    else t cat:= c; end if;
  end for;
  return "\"" cat t cat "\"";
end function;

function JVal(v)
  case Type(v):
    when MonStgElt: return JStr(v);
    when RngIntElt: return IntegerToString(v);
    when BoolElt:   return v select "true" else "false";
    when FldRatElt: return JStr(Sprint(v));            // rationals as strings: exact
    when SeqEnum:   return "[" cat (#v eq 0 select "" else &cat[JVal(v[i]) cat (i lt #v select "," else "") : i in [1..#v]]) cat "]";
    when List:
      if #v gt 0 and &and[Type(v[i]) eq Tup and #v[i] eq 2 and Type(v[i][1]) eq MonStgElt : i in [1..#v]] then
        return "{" cat &cat[JStr(v[i][1]) cat ":" cat JVal(v[i][2]) cat (i lt #v select "," else "") : i in [1..#v]] cat "}";
      end if;
      return "[" cat (#v eq 0 select "" else &cat[JVal(v[i]) cat (i lt #v select "," else "") : i in [1..#v]]) cat "]";
  end case;
  return JStr(Sprint(v));
end function;

function JObj(pairs)   // pairs: list of <key, value>
  return "{" cat (#pairs eq 0 select "" else &cat[JStr(pairs[i][1]) cat ":" cat JVal(pairs[i][2]) cat (i lt #pairs select "," else "") : i in [1..#pairs]]) cat "}";
end function;

procedure Emit(pairs)
  Write(OutFile, JObj(pairs) : Overwrite := true);
end procedure;

procedure Fail(reason, pairs)
  Log("FAIL: " cat reason);
  Emit([* <"ok", false>, <"error", reason> *] cat pairs);
end procedure;

// ---------------------------------------------------------------- helpers
function Coeffs(v)          // element of K -> coefficient list (strings) w.r.t. the power basis
  return [Sprint(c) : c in Eltseq(v)];
end function;

function PolyString(f, var)
  P<xx> := PolynomialRing(BaseRing(Parent(f)));
  s := Sprint(P!Eltseq(f));
  return SubstituteString(s, "xx", var);
end function;

function ElementString(v)   // element of K as a polynomial in a (Magma's own printing)
  return Sprint(v);
end function;

function FactoredString(N)  // integer -> "-1 * 2^2 * 3 * 139^2"
  if N eq 0 then return "0"; end if;
  parts := [];
  if N lt 0 then Append(~parts, "-1"); end if;
  for t in Factorization(Abs(N)) do
    Append(~parts, t[2] eq 1 select Sprint(t[1]) else Sprintf("%o^%o", t[1], t[2]));
  end for;
  if #parts eq 0 then return "1"; end if;
  return &cat[parts[i] cat (i lt #parts select " * " else "") : i in [1..#parts]];
end function;

function HasExactOrder(pt, k)
  if not IsZero(k*pt) then return false; end if;
  for p in PrimeDivisors(k) do
    if IsZero((k div p)*pt) then return false; end if;
  end for;
  return true;
end function;

// Tate normal form of (E, Q), Q of order >= 4.  Magma's Transformation(E,[r,s,t,u]) is
// x' = u^2 x + r, y' = u^3 y + s u^2 x + t.
function TateNormalForm(E, Q)
  E1, f1 := Transformation(E, [-Q[1], 0, -Q[2], 1]);          // Q -> (0,0)
  a := aInvariants(E1);
  error if a[5] ne 0, "Tate normal form: (0,0) not on the curve";
  error if a[3] eq 0, "Tate normal form: Q has order 2";
  s := a[4]/a[3];
  E2, f2 := Transformation(E1, [0, -s, 0, 1]);                // kills a4
  a := aInvariants(E2);
  error if a[2] eq 0, "Tate normal form: Q has order 3";
  v := a[2]/a[3];
  E3, f3 := Transformation(E2, [0, 0, 0, v]);                 // a2 = a3
  a := aInvariants(E3);
  b := -a[2]; c := 1 - a[1];
  error if aInvariants(E3) ne [1-c, -b, -b, 0, 0], "Tate normal form: internal error";
  return E3, b, c, f1*f2*f3;
end function;

// ---------------------------------------------------------------- 0. sanity
Log(Sprintf("start: X_1(%o,%o) mode=%o", m, n, mode));
if Type(m) eq MonStgElt then m := StringToInteger(m); end if;
if Type(n) eq MonStgElt then n := StringToInteger(n); end if;
if n mod m ne 0 or n lt 4 then
  Fail(Sprintf("need m | n and n >= 4 (got m=%o, n=%o)", m, n), [* *]); quit;
end if;

// ---------------------------------------------------------------- 1. the field
Qx<x> := PolynomialRing(Rationals());
ok := true;
try
  f := Qx!(eval fpoly);
catch e
  ok := false;
end try;
if not ok or Degree(f) lt 1 then Fail("could not parse the field polynomial", [* *]); quit; end if;
if not IsIrreducible(f) then Fail("the field polynomial is reducible over Q", [* <"fpoly", Sprint(f)> *]); quit; end if;
K<a> := NumberField(f);
d := Degree(K);
Log(Sprintf("field: degree %o, %o", d, f));

// ---------------------------------------------------------------- 2. the curve and the points
E := 0; P := 0; Q := 0; haveP := false; haveQ := false;
ok := true; msg := "";
try
  case mode:
    when "ainvs":
      ai := [K | eval s : s in ainvs];
      E := EllipticCurve(ai);
    when "tate":
      b0 := K!(eval tb); c0 := K!(eval tc);
      E := EllipticCurve([K | 1-c0, -b0, -b0, 0, 0]);
      Q := E![0,0]; haveQ := true;
    when "vanhoeij":
      // fpoly = eqx(x); eqxy(x,y) = 0 defines y0 over Q(x0).  Residue field Q(x0,y0).
      Kxy<X, Y> := PolynomialRing(K, 2);
      g := eval SubstituteString(SubstituteString(eqxy, "x", "X"), "y", "Y");
      gy := UnivariatePolynomial(Evaluate(Kxy!g, 1, K!a));      // polynomial in y over K
      // take the first irreducible factor over K; van Hoeij lists a place, any factor gives a conjugate
      fac := Factorization(gy);
      h := fac[1][1];
      if Degree(h) eq 1 then
        y0 := -Coefficient(h, 0)/Coefficient(h, 1);
        KK := K; x0 := K!a;
      else
        Krel<yy> := NumberField(h);
        KK := AbsoluteField(Krel);
        x0 := KK!(Krel!a); y0 := KK!(Krel.1);
      end if;
      r := (x0^2*y0 - x0*y0 + y0 - 1)/(x0^2*y0 - x0);
      s := (x0*y0 - y0 + 1)/(x0*y0);
      b0 := r*s*(r-1); c0 := s*(r-1);
      // rewrite K as the (possibly bigger) absolute field so that everything below is over K
      K := KK; d := Degree(K);
      if Degree(KK) gt Degree(f) then
        Log(Sprintf("van Hoeij format: y-equation has degree %o over Q(x0); absolute field of degree %o", Degree(h), d));
      end if;
      E := EllipticCurve([K | 1-c0, -b0, -b0, 0, 0]);
      Q := E![0,0]; haveQ := true;
    else
      ok := false; msg := "unknown mode " cat mode;
  end case;
catch e
  ok := false; msg := "could not build the elliptic curve: " cat Sprint(e`Object);
end try;
if not ok then Fail(msg, [* *]); quit; end if;
Log(Sprintf("curve: %o", aInvariants(E)));

// optional explicit points
try
  if #Qxy eq 2 then
    Q := E![K | eval Qxy[1], eval Qxy[2]]; haveQ := true;
  end if;
  if #Pxy eq 2 then
    P := E![K | eval Pxy[1], eval Pxy[2]]; haveP := true;
  end if;
catch e
  Fail("a given point does not lie on the curve: " cat Sprint(e`Object), [* *]); quit;
end try;

// ---------------------------------------------------------------- 3. find Q (order n) and P (order m) if not given
torsion_inv := [];
torsion_known := false;
if not haveQ or (m gt 1 and not haveP) then
  if SkipFullTorsion then
    Fail("points P, Q not given and full torsion computation disabled", [* *]); quit;
  end if;
  Log("computing E(K)_tors to find the points (this is the slow step; give P and Q to avoid it)");
  T, mT := TorsionSubgroup(E);
  torsion_inv := Invariants(T); torsion_known := true;
  Log(Sprintf("E(K)_tors = %o", torsion_inv));
  if not haveQ then
    cands := [mT(g) : g in T | Order(g) eq n];
    if #cands eq 0 then
      Fail(Sprintf("E(K) has no point of order %o (E(K)_tors = %o)", n, torsion_inv), [* <"torsion_invariants", torsion_inv> *]); quit;
    end if;
    Q := cands[1]; haveQ := true;
  end if;
  if m gt 1 and not haveP then
    found := false;
    for g in T do
      if Order(g) ne m then continue; end if;
      Pc := mT(g);
      // <P,Q> has order mn  <=>  P and (n/m)Q are independent in E[m]
      S := {k*Pc + l*((n div m)*Q) : k in [0..m-1], l in [0..m-1]};
      if #S eq m^2 then P := Pc; found := true; break; end if;
    end for;
    if not found then
      Fail(Sprintf("no point P of order %o with <P,Q> = Z/%o x Z/%o (E(K)_tors = %o)", m, m, n, torsion_inv), [* <"torsion_invariants", torsion_inv> *]); quit;
    end if;
    haveP := true;
  end if;
end if;
if m eq 1 then P := E!0; haveP := true; end if;

// ---------------------------------------------------------------- 4. verify the orders and the structure
if not HasExactOrder(Q, n) then Fail(Sprintf("Q does not have exact order %o", n), [* *]); quit; end if;
if not HasExactOrder(P, m) then Fail(Sprintf("P does not have exact order %o", m), [* *]); quit; end if;
if m gt 1 then
  S := {k*P + l*((n div m)*Q) : k in [0..m-1], l in [0..m-1]};
  if #S ne m^2 then Fail(Sprintf("<P,Q> is not Z/%o x Z/%o (P lies in <Q> + smaller)", m, n), [* *]); quit; end if;
end if;
Log(Sprintf("orders verified: ord P = %o, ord Q = %o, <P,Q> = Z/%o x Z/%o", m, n, m, n));

// ---------------------------------------------------------------- 5. torsion bound from reductions
OK := MaximalOrder(K);
DE := Discriminant(E);
bound := 0; used := [];
for p in PrimesInInterval(3, 400) do
  if bound eq m*n then break; end if;
  for pr in Decomposition(OK, p) do
    if InertiaDegree(pr[1]) ne 1 or RamificationIndex(pr[1]) ne 1 then continue; end if;
    if Valuation(DE, pr[1]) ne 0 then continue; end if;
    if exists{ai : ai in aInvariants(E) | ai ne 0 and Valuation(ai, pr[1]) lt 0} then continue; end if;
    Ep := Reduction(E, pr[1]);
    bound := GCD(bound, #Ep);
    Append(~used, p);
    break;   // one prime above p suffices
  end for;
end for;
if bound eq 0 then bound := -1; end if;
Log(Sprintf("torsion bound from reductions: |E(K)_tors| divides %o (primes %o)", bound, used));
if bound eq m*n then
  torsion_inv := m eq 1 select [n] else [m, n]; torsion_known := true;
elif not torsion_known and not SkipFullTorsion then
  Log("torsion may be larger than <P,Q>: computing E(K)_tors");
  T := TorsionSubgroup(E);
  torsion_inv := Invariants(T); torsion_known := true;
  Log(Sprintf("E(K)_tors = %o", torsion_inv));
end if;

// ---------------------------------------------------------------- 6. Tate normal form and residue field
ok := true;
try
  Et, b, c, iso := TateNormalForm(E, Q);
catch e
  ok := false; msg := Sprint(e`Object);
end try;
if not ok then Fail("Tate normal form failed: " cat msg, [* *]); quit; end if;
Pt := iso(P);
gensL := [b, c] cat (m gt 1 select [Pt[1], Pt[2]] else [K | ]);
L := sub<K | gensL>;
dL := Degree(L);
Log(Sprintf("Tate normal form done; residue field of the point has degree %o (K has degree %o)", dL, d));
// express the point over its residue field L
if dL eq 1 then
  Lopt := L; mopt := map<L -> L | v :-> v>;
else
  Lopt, mopt := OptimizedRepresentation(L);
end if;
bL := mopt(L!b); cL := mopt(L!c);
PtL := m gt 1 select [mopt(L!(Pt[1])), mopt(L!(Pt[2]))] else [Lopt | ];
fL := DefiningPolynomial(Lopt);

// ---------------------------------------------------------------- 7. invariants
j := jInvariant(E);
jmin := MinimalPolynomial(j);
jdeg := Degree(jmin);
jrat := jdeg eq 1 select Sprint(Rationals()!Eltseq(j)[1]) else "";
cmflag := false; cmdisc := 0;
try
  cmflag := HasComplexMultiplication(E);
  if cmflag then _, cmdisc := HasComplexMultiplication(E); end if;
catch e
  Log("HasComplexMultiplication failed: " cat Sprint(e`Object));
end try;
Log(Sprintf("j: degree %o, CM %o %o", jdeg, cmflag, cmdisc));
dn := Norm(Discriminant(E));
disc_norm := Sprint(Numerator(dn)) cat (Denominator(dn) eq 1 select "" else "/" cat Sprint(Denominator(dn)));
cond_norm := "";
if Abs(Numerator(dn)) lt 10^40 and Abs(Denominator(dn)) lt 10^40 then
  try
    Emin := MinimalModel(E);
    cond_norm := Sprint(Norm(Conductor(Emin)));
    Log("conductor norm " cat cond_norm);
  catch e
    Log("conductor not computed: " cat Sprint(e`Object));
  end try;
end if;
OL := MaximalOrder(Lopt);
discL := Discriminant(OL);
r1, r2 := Signature(Lopt);
v1, v2, v3 := GetVersion();
ver := Sprintf("%o.%o-%o", v1, v2, v3);

// ---------------------------------------------------------------- 8. output
Emit([*
  <"ok", true>,
  <"m", m>, <"n", n>,
  <"magma_version", ver>,
  <"submitted_field", [* <"poly", PolyString(f, "x")>, <"degree", Degree(f)> *]>,
  <"working_field", [* <"poly", PolyString(DefiningPolynomial(K), "x")>, <"degree", d> *]>,
  <"curve", [*
      <"ainvs", [ElementString(v) : v in aInvariants(E)]>,
      <"ainvs_coeffs", [Coeffs(v) : v in aInvariants(E)]>,
      <"j", ElementString(j)>, <"j_rational", jrat>,
      <"j_minpoly", PolyString(jmin, "x")>, <"j_degree", jdeg>,
      <"cm", cmflag>, <"cm_disc", cmdisc>,
      <"disc_norm", disc_norm>, <"conductor_norm", cond_norm>
  *]>,
  <"points", [* <"P", [ElementString(P[1]), ElementString(P[2])]>, <"Q", [ElementString(Q[1]), ElementString(Q[2])]>,
               <"order_P", m>, <"order_Q", n> *]>,
  <"torsion", [* <"invariants", torsion_inv>, <"known_exactly", torsion_known>, <"order_bound", bound>,
                <"bound_primes", used>, <"contains_Zm_x_Zn", true> *]>,
  <"tate", [* <"b", ElementString(b)>, <"c", ElementString(c)>,
             <"P", m gt 1 select [ElementString(Pt[1]), ElementString(Pt[2])] else [] > *]>,
  <"residue_field", [*
      <"degree", dL>, <"equals_K", dL eq d>,
      <"poly", PolyString(fL, "x")>, <"poly_coeffs", [Sprint(cc) : cc in Coefficients(fL)]>,
      <"disc", Sprint(discL)>, <"disc_factored", FactoredString(discL)>,
      <"signature", [r1, r2]>,
      <"b", Sprint(bL)>, <"c", Sprint(cL)>, <"b_coeffs", Coeffs(bL)>, <"c_coeffs", Coeffs(cL)>,
      <"P", [Sprint(v) : v in PtL]>, <"P_coeffs", [Coeffs(v) : v in PtL]>
  *]>,
  <"cputime", RealField(6)!Cputime(T0)>
*]);
Log("VERIFY_DONE");
