# anchor_ussr: notes (branch "anchor_ussr")

## STATUS: MOSTLY BLOCKED. This is a partial, honest record, not a completed audit.
- WebFetch failed with a DNS error (getaddrinfo ENOTFOUND) for every host tried, including example.com,
  ntrs.nasa.gov, engine.space and astronautix.com.
- curl through the egress proxy got a 403 CONNECT for every host probed. Per the proxy README, an org-policy
  403 must not be routed around.
- After only 2 searches from this branch, the shared WebSearch budget (200 per turn across all agents) was used up.
- Result: no document was opened. Every source in sources.json is `search_result_only` or `not_retrieved`.
  Locators are URL-level only. Some value-to-source pairings come from the search model's summary and are
  ambiguous; these are flagged in the notes and in conflicts.json (CF-4 and CF-5).
- No schematics were viewed, so schematics.json is empty.
- 7 of the 8 anchors have empty assertion lists and no topology. Each has a `verification_targets_unsourced` list.
  That list holds the orchestrator's hypotheses plus my unverified recall, to check on a re-run. It is not data.

## Per anchor
- **RD-180 (ENG-RU-RD-180)**: the only anchor with data. It has 30 assertions from the excerpts of the P&W fact
  sheet as reprinted by Spaceflight Now, the Purdue page, the Glavkosmos trade page and Russian press.
  Cycle reported: "LOx rich, closed cycle, staged combustion". Other reported values: 2 chambers gimballed +-8 deg,
  throttle 47-100%, and 70% parts commonality with RD-170. Conflicts: Pc 3722 psia vs 3734 psia vs 261 kgf/cm2
  (CF-1), throttle 47% vs 40% (CF-3), area ratio 36.87 vs 36.4 (CF-4), O/F 2.72 vs 2.6 (CF-5), and mass
  11,675 lb vs 5,480 kg dry (CF-6). The key Tier B source, the ULA-hosted paper "RD-180 Engine: An Established
  Record of Performance and Reliability on Atlas Launch Vehicles", was seen as a URL but could not be opened.
  The topology has 2 chambers plus one INFERRED ox-rich preburner node and 2 INFERRED closed-cycle edges.
- **RD-170 (ENG-RU-RD-170)**: The only values found are Pc 266.7 bar, from Russian journalism quoting "published
  Energomash data", and the chief designer's claim of >280 bar margin. CF-2 records that the claim is a design margin,
  not a rated value. The **1-vs-2 preburner question is UNRESOLVED**: no source on it was retrieved. RD-171 and
  RD-171M exist only as placeholder records in engines.json.
- **NK-33 / AJ26-62, RD-0120, RD-107A / RD-108A, RD-270, RD-0124, A-4**: nothing was retrieved for any of these.
  The anchor files hold scope, schema-breaker hypotheses and verification targets only. The native indices
  (11D521, 11D111, 11D122, 14D22, 8D420, 14D23) come from the task prompt and are unverified; their alias
  `source_ids` are empty.

## Schema breakers worth keeping, even unverified
- Several chambers fed by one turbomachinery set: RD-170 (4), RD-180 (2), RD-0124 (4) and RD-107/108. Gimbal is
  per chamber while thrust and Pc are per engine.
- Chamber counts by role: RD-107A has 4 main + 2 vernier chambers and RD-108A has 4 + 4. One integer cannot hold this.
- A third, turbine-only working fluid (H2O2 steam generator) in RD-107/108 and A-4. A-4 also has a catalyst consumable.
- Stage-serving equipment on the engine, such as the LN2 evaporator for tank pressurisation on RD-107/108.
- Value kinds: a rated value vs a claimed design margin (RD-170 Pc), and throttle range given 3 ways.
- A mass-definition qualifier: "weight" vs "dry mass".
- Cross-company re-designation with modifications (NK-33 -> AJ26-62).
- A fuel given as a concentration (A-4 ethanol mixture).

## For the re-run (priority order)
1. ULA/AIAA RD-180 record paper: preburner count, boost pump drives, ignition.
2. engine.space pages for RD-170, RD-171M, RD-180, RD-107A/108A and RD-270, plus schematics.
3. NTRS: P&W/KBKhA RD-0120 papers, and the Orb-3 IRT public summary for AJ26.
4. kbkha.ru for RD-0120 and RD-0124. kuznetsov-motors.ru for NK-33.
5. NASA MSFC / US Army A-4 documents.
Use the Russian queries suggested in the task prompt.
