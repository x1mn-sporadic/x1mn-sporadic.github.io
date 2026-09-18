/* isolation_batch.m -- isolation checks for many points of the same curve X_1(m,n) in one process,
   sharing the models over F_q (whose integral closures dominate the cost).
   Job file defines: m, n, MdmagmaSpec, ModelsDir, LogFile, OutFile, MaxPrimes (optional), and
     POINTS := [ <id, fpoly, tb, tc, Px, Py>, ... ];
   Results are appended to OutFile one JSON line per point ({"id": ..., ...}) as they are obtained,
   so that a killed run keeps what it has done. */
load "/home/fnajman/webpage_sporadic/pipeline/magma/isolation_lib.m";
if Type(m) eq MonStgElt then m := StringToInteger(m); end if;
if Type(n) eq MonStgElt then n := StringToInteger(n); end if;
cache := AssociativeArray();
for pt in POINTS do
  id := pt[1];
  Log(Sprintf("=== %o", id));
  json := "";
  try
    IsolationCheck(m, n, pt[2], pt[3], pt[4], pt[5], pt[6], MaxPrimes, ~cache, ~json);
  catch e
    json := Sprintf("{\"ok\": false, \"error\": \"%o\"}", e`Object);
    Log("FAIL: " cat Sprint(e`Object));
  end try;
  Write(OutFile, Sprintf("{\"id\": \"%o\", \"result\": %o}", id, json));
end for;
Log("BATCH_DONE");
quit;
