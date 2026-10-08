# DB-0.5 — status: BLOCKED (no document access)

DB-0.5 requires opening primary sources and viewing schematics. In the session
that produced this file the egress policy refused every documentation host
(`ntrs.nasa.gov`, `apps.dtic.mil`, `patents.google.com`, `www.ibiblio.org`,
`en.wikipedia.org`, `arxiv.org`) and WebFetch could not resolve any host. No
document was opened, no schematic viewed, and no assertion promoted. Gates A–E
are therefore **not passed**; DB-0 remains PARTIAL and its values stay
`SEARCH_RESULT_ONLY` / `SECONDARY_CLAIM`.

To unblock: add the hosts above (and agency/manufacturer hosts such as
`www.l3harris.com`, `iafastro.directory`, `repository.exst.jaxa.jp`) under
Network access in the cloud environment settings.

`work_queue.json` is the only DB-0.5 artifact so far. It is generated offline
from the DB-0 corpus and verifies nothing: 124 Tier A/B documents to open
(62 P0), 71 schematic leads to inspect (35 P0), 206 unresolved conflicts
(36 P0). P0 = attached to a priority anchor (RS-25, J-2/J-2S, F-1, H-1, RL10,
Apollo SPS/LMDE, OMS, IPD, RD-170, LR87, Rutherford, RS-68A).
