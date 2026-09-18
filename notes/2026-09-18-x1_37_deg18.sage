import json
E = EllipticCurve('1225h2'); Es = E.short_weierstrass_model()
h = Es.isogenies_prime_degree(37)[0].kernel_polynomial()
R.<x> = QQ[]
hb = R(pari(h).polredbest())
K.<a> = NumberField(hb)
# root of h in K
roots = h.change_ring(K).roots(multiplicities=False); assert roots, "no root of kernel poly in polredbest field"
x0 = roots[0]
A4, A6 = Es.a4(), Es.a6()
D = x0^3 + A4*x0 + A6
assert not D.is_square()
Et = EllipticCurve(K, [0,0,0, A4*D^2, A6*D^3]); P = Et(D*x0, D^2)
assert (37*P).is_zero() and not P.is_zero()
assert Et.j_invariant() == E.j_invariant()
def magma_str(e):
    # element of K as polynomial in a with integer coefficients over common denominator
    s = str(e.polynomial()).replace('x','a').replace(' ','')
    return s
sub = {
 "schema": "x1mn-sporadic/submission/1",
 "m": int(1), "n": int(37),
 "field": str(hb).replace(' ',''),
 "curve": {"ainvs": [magma_str(c) for c in Et.ainvs()]},
 "points": {"Q": [magma_str(P[0]), magma_str(P[1])]},
 "degree": int(18),
 "expected": {"j_degree": int(1), "j": str(E.j_invariant())},
 "discoverer": "A. Bourdon, S. Hashimoto, T. Keller, Z. Klagsbrun, D. Lowry-Duda, T. Morrison, F. Najman, H. Shukla (isolation; AV-isolation in the appendix by M. Derickx and M. van Hoeij)", "year": int(2023),
 "submitter": "Filip Najman", "affiliation": "University of Zagreb", "github": "F-Najman",
 "reference": "A. Bourdon, S. Hashimoto, T. Keller, Z. Klagsbrun, D. Lowry-Duda, T. Morrison, F. Najman, H. Shukla, Towards a classification of isolated j-invariants, Math. Comp. 94 (2025), 447-473, arXiv:2311.07740 (with an appendix by M. Derickx and M. van Hoeij); see also A. Bourdon, O. Ejder, Rational isolated j-invariants from X_1(l^n) and X_0(l^n), arXiv:2506.19560, Theorem 4. The point itself (degree 18, not sporadic since gon_Q X_1(37) = 18) is noted in Bourdon-Ejder-Liu-Odumodu-Viray, Adv. Math. 357 (2019), proof of Theorem 8.1, and in Sutherland's 2012 notes.",
 "notes": "The rational elliptic curve 1225.h2 (Cremona 1225h2, j = -7*137^3*2083^3 = -162677523113838677) has a rational 37-isogeny; the x-coordinates of the kernel points generate a totally real field K of degree 18 (disc 5^9*7^12*37^17), and the quadratic twist of 1225h2 by D = x0^3 + A4*x0 + A6 (short model) has the K-rational point Q = (D*x0, D^2) of order 37. Submitted curve = that twist over K = Q(a), a a root of the polredbest polynomial of the kernel polynomial. The point has degree 18 = gon_Q(X_1(37)), so it is not sporadic; it is isolated (P^1-isolated and AV-isolated) by the reference. Prepared 2026-09-18 during a literature check; not yet verified by the census pipeline.",
}
json.dump(sub, open('x1_37_deg18_submission.json','w'), indent=1)
print(json.dumps({k:v for k,v in sub.items() if k in ('field','degree','expected')}, indent=1))
print("ainvs lengths:", [len(s) for s in sub['curve']['ainvs']], "Q lengths:", [len(s) for s in sub['points']['Q']])
print("sanity: order of Q =", P.order())
