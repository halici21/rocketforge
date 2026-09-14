# Security Policy

RocketForge is a desktop engineering application with no network surface of
its own — it does not open a server, accept remote input, or phone home.
Realistic report categories are things like: a dependency pulled in by
`requirements*.txt` with a known CVE, a path-handling bug in the packaged
build (`packaging/RocketForge.spec`) that could be abused via a crafted
project file, or an issue in how the NASA CEA / CoolProp native libraries are
loaded.

## Reporting a vulnerability

Please **do not** open a public issue for a security concern. Use GitHub's
private reporting instead:

[Report a vulnerability](https://github.com/halici21/rocketforge/security/advisories/new)
(Security tab → Advisories → "Report a vulnerability")

This is a solo-maintained project — response time is best-effort, not
SLA-backed, but every report will get a reply.

## Supported versions

There are no tagged releases with a support matrix yet; the `master` branch
is the only supported line. Report against the latest commit.
