# Design Skill Foundation R1 — Security review

Every skill installed under `.claude/skills/` was inspected before
installation, not after. Agent Skills carry substantial code access and were
treated as executable development dependencies throughout this review, per
the brief's own framing.

## Method

For each candidate seriously considered for installation:

1. Listed every file in the skill's directory (`gh api
   repos/OWNER/REPO/contents/...` or a shallow `git clone`), not just
   `SKILL.md`.
2. Read every script file in full or, for one large file, confirmed its
   import list and scanned for dangerous call patterns
   (`subprocess`, `os.system`, `eval`/`exec`, `urllib`/`requests`/`socket`,
   destructive filesystem calls, unexpected file writes).
3. Checked for auto-install commands, network calls, credential access, or
   global (outside-repository) file writes in any bundled script or in the
   `SKILL.md` instructions themselves.
4. Confirmed nothing was installed to `~/.claude/skills/` or any location
   outside this repository's `.claude/skills/`.

## Installed skills — findings

| Skill | Scripts present | Findings |
| --- | --- | --- |
| `qt-qml` | None | Pure markdown (`SKILL.md`, `README.md`, a Windsurf-specific prompt variant). No executable content. |
| `qt-ui-design` | None | Pure markdown. No executable content. |
| `qt-qml-review` | `references/lint-scripts/qt_qml_lint.py` (1486 lines) | Read in full. Imports only `json`, `re`, `sys`, `dataclasses`, `pathlib`, `typing` — Python standard library only. No `subprocess`, no network module, no `eval`/`exec`, no file-write calls beyond normal stdout. It is a static, read-only source-text linter: reads `.qml` files passed as arguments, prints `FILE:LINE RULE-ID MESSAGE` or a JSON report, exits 0/1 by finding count. Confirmed the invocation documented in `SKILL.md` (`python3 references/lint-scripts/qt_qml_lint.py <files...>`) matches this behaviour — nothing hidden or undocumented. **Clean.** |
| `design-review` | None | Pure markdown (`SKILL.md`, `references/review-rubric.md`). No executable content, no network calls documented (image/screenshot handling is delegated to the invoking agent's own capabilities, not to a bundled fetcher). |

No installed skill contains a shell command that installs software, makes a
network call, modifies global configuration, accesses credentials, or
writes outside the repository. No installed skill's `SKILL.md` instructs
the invoking agent to do any of these either.

## Reference-only candidates — findings

Not installed, so their code was not given execution trust, but each was
still inspected to confirm the reference-only decision itself was not
concealing a reason to reject outright:

- `frontend-design` (anthropics) — pure markdown, Apache-2.0. No concerns;
  not installed for platform-mismatch reasons only, not security ones.
- `tufte-claude-skill` (aref-vc) — markdown plus static HTML/PDF assets
  (`before-after.html`, `cheatsheet.html/pdf`, `presets/`). No scripts. No
  concerns.
- `qt-qml-profiler` (TheQtCompanyRnD) — contains
  `references/scripts/parse-qmlprofiler-trace.py` and build-orchestration
  logic that shells out to `cmake`/`qmlprofiler`/the built executable. Not
  installed because its automation assumes a CMake build this project does
  not have (a compatibility rejection); no evidence of malicious intent —
  it is exactly what its description says, a build-and-profile
  orchestrator, scoped to a build system this project isn't on.
- `better-*` family (jakubkrehel) — pure markdown across all seven
  skills read. No scripts, no concerns; not installed for platform-mismatch
  reasons only.

## Rejected candidates — findings

- `Cai-aa/CAD-Agent-Hub`, `Cai-aa/CAE-Agent-Hub` — both bundle real MCP
  servers that automate commercial engineering software (CATIA, Abaqus,
  ANSYS). These were rejected as off-topic before any code-level security
  review, since they were never going to be installed regardless of
  code quality — automating a different program entirely is outside this
  run's scope.
- `NVIDIA/skills` — noted a repository-root file,
  `nv-agent-root-cert.pem`, whose purpose (a trust anchor for some part of
  NVIDIA's own plugin/skill distribution mechanism) was not investigated
  further, because the repository's content (CUDA/DeepStream/GPU tooling)
  was already off-topic and not a candidate for installation regardless.
  Flagged here only so the observation is on record, not because it blocked
  a decision that had already been made on relevance grounds.
- `violet-hgy/agent-skills-qt-quick-qml`, `bigzhuodan/claude-skill-qt-design`,
  `AJpon/qt-python-ai-skills` — zero-star, unlicensed-or-unclear,
  single-contributor repositories. Not opened past metadata/README level:
  given a strictly superior, officially-licensed, higher-adoption
  alternative (`TheQtCompanyRnD/agent-skills`) already covering the same
  ground, the marginal value of a full code-level audit of three unvetted
  repositories was judged not worth the review cost. This is a
  **confidence-based pass**, not a positive finding of safety — if a future
  need makes one of these specifically relevant, audit it properly before
  installing rather than relying on this note.

## Outcome

No installed skill required a security exception, a scope restriction, or
a modification before installation. Everything installed is either pure
markdown or a confirmed-clean, stdlib-only, read-only static analysis
script.
