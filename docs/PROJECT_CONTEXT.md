# CodeImpact project context

Owner: GitHub **danielpan01**. Goal: a memorable, practical SWE portfolio project
with an original analysis component the owner can defend in an interview.

Origin: the “Vibe Coding Ideas” conversation proposed a Python-first PR impact
explorer: changed functions, potential downstream effects and relevant tests.

## Locations and ownership

- GitHub: https://github.com/danielpan01/codeimpact — created private, initially empty.
- Local working tree created by setup:
  `/Users/danny/Documents/Codex/2026-11-05/referenced-chatgpt-conversation-this-is-an/outputs/codeimpact`
- ChatGPT project: **CodeImpact** (`g-p-6aed253d2ef88191b129b52d050ea7b7`).
- Cloud Work chat: **CodeImpact Project Orientation**:
  https://chatgpt.com/c/6aed2816-95c0-83e8-9ff8-682f88b76275

The cloud chat was created inside the existing project and its context reply was
verified. Phone access itself was not tested. Open the same ChatGPT account on web
or phone and find the chat in CodeImpact. A cloud conversation does not automatically
mirror this Mac folder. The user must push reviewed changes before GitHub can serve
as the shared source of truth. GitHub connector access to the new private repository
was verified during setup for this new private repo. After the first push, verify
that the cloud chat can retrieve the actual files; account connection alone does
not guarantee that every execution environment can clone them.

The setup agent does not stage, commit or push the project. User Git identity is
left unchanged. Test fixtures create synthetic commits in temporary directories
using an explicitly fictional fixture identity, never in this project repository.

## Current scope

Working local vertical slice: AST graph, semantic snapshot comparison, deleted-node
preservation, conservative impact traversal, ranked evidence paths, Git CLI,
FastAPI, responsive React graph, demo, upload/export, pinned dependencies, tests,
lint/type checking and CI configuration. Consult VALIDATION.md for actual results.

Not implemented: live PR URL ingestion, GitHub App auth, durable jobs, source caching,
database, public hosted app, production abuse controls or a real-repository accuracy
benchmark. Do not present those as existing features.

## Model and cross-device settings

User preference: **GPT-6 Astra, Extra high**. The cloud creation tool does not accept
model or reasoning overrides, so setup did not switch or verify those settings.
Choose Astra in the chat's model selector and Extra high in its reasoning controls
if offered by the account. Availability varies by client and workspace.

Official guidance describes cloud Work and eligible synced conversations across
devices. Local access through a synced conversation depends on the workspace setting
and a connected computer. This setup uses a cloud chat plus a separate local working
tree; no local-computer sync setting was changed or verified.

Sources checked during setup:
[Work and cross-device behavior](https://learn.chatgpt.com/docs/get-started-with-work),
[model and effort selection](https://learn.chatgpt.com/docs/model-selection).

## Build strategy

Use Codex to implement bounded slices. Review and understand each before making your
own commit. Sequence: own the engine → labeled correctness corpus → real public PR
ingestion → durable jobs/private authorization/deployment → measured evaluation.

Most impressive evidence: show a real change, traverse its dependency path to a test,
retain deleted dependencies, label uncertainty, compare against known affected tests,
and report honest measurements. Avoid invented resume metrics and unsupported claims
that selected tests can safely replace the complete suite.
