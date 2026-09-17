/* curve_invariants.m -- genus and PSL_2(Z)-index of every curve in the census list.
   Gamma_1(m,n) = Gamma(m) meet Gamma_1(n) is Magma's CongruenceSubgroup([n, n, m]).
   Run from the repository root:  magma -b pipeline/magma/curve_invariants.m < /dev/null
   Writes data/knowledge/curves_magma.json. */
SetColumns(0);
list := [];
for n in [1..100] do Append(~list, <1, n>); end for;
for n in [2..60 by 2] do Append(~list, <2, n>); end for;
for n in [3..39 by 3] do Append(~list, <3, n>); end for;
for n in [4..36 by 4] do Append(~list, <4, n>); end for;
for n in [5..20 by 5] do Append(~list, <5, n>); end for;
for n in [6..18 by 6] do Append(~list, <6, n>); end for;
for n in [7..14 by 7] do Append(~list, <7, n>); end for;
for n in [8..16 by 8] do Append(~list, <8, n>); end for;
Append(~list, <9, 9>); Append(~list, <10, 10>);
v1, v2, v3 := GetVersion();
out := Sprintf("{\"magma_version\": \"%o.%o-%o\", \"group\": \"CongruenceSubgroup([n,n,m]) = Gamma(m) meet Gamma_1(n)\", \"curves\": [\n", v1, v2, v3);
for i in [1..#list] do
  m := list[i][1]; n := list[i][2];
  G := CongruenceSubgroup([n, n, m]);
  out cat:= Sprintf("  {\"m\": %o, \"n\": %o, \"genus\": %o, \"index\": %o}%o\n", m, n, Genus(G), Index(G), i lt #list select "," else "");
end for;
out cat:= "]}\n";
Write("data/knowledge/curves_magma.json", out : Overwrite := true);
print "CURVES_DONE", #list;
quit;
