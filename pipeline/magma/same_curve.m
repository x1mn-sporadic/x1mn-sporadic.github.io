/* same_curve.m -- are two elliptic curves, given over two (abstractly isomorphic) number fields,
   the same curve up to an isomorphism of the fields?  Used by verify.py to record a point once
   per elliptic curve over its residue field: two level structures on isomorphic curves differ by
   a diamond operator, by the choice of the torsion basis, or by Galois conjugation.
   Job file defines: fpoly1, ainvs1 (5 strings in a), fpoly2, ainvs2, OutFile.  Writes {"same": true|false}. */
Qx<x> := PolynomialRing(Rationals());
K1<a> := NumberField(Qx!(eval fpoly1));
E1 := EllipticCurve([K1 | eval s : s in ainvs1]);
K2<a> := NumberField(Qx!(eval fpoly2));
E2 := EllipticCurve([K2 | eval s : s in ainvs2]);
same := false;
ok, iso := IsIsomorphic(K2, K1);
if ok then
  E2t := EllipticCurve([iso(c) : c in aInvariants(E2)]);
  for s in Automorphisms(K1) do
    Es := EllipticCurve([s(c) : c in aInvariants(E2t)]);
    if IsIsomorphic(Es, E1) then same := true; break; end if;
  end for;
end if;
Write(OutFile, same select "{\"same\": true}" else "{\"same\": false}" : Overwrite := true);
quit;
