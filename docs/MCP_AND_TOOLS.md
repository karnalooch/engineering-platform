# MCP and tool capability contract

Status: **ACTIVE / AUTHORITATIVE**

## Principle

Gumball describes **capabilities and trust boundaries**, not a mandatory shopping list of tools.

A project should enable only the tools needed for its work. Tool selection and lifecycle follow [TOOLING_AUTHORITY.md](TOOLING_AUTHORITY.md): proven/reference tooling and platform-native capability are evaluated before custom tooling, and accepted authority must have a deterministic repository return path.

## Capability classes

Typical classes:

- source control / GitHub;
- filesystem and code search;
- browser / documentation lookup;
- issue and project management;
- database inspection;
- runtime/editor control;
- build/test runners;
- artifact inspection.

Technology-specific integrations belong in profiles or consumer repositories. For example, Unreal editor control is useful to an Unreal profile but should not become a baseline dependency for a web service.

## Safety rules

- Tool access never overrides repository policy.
- Secrets and credentials must not be committed to tool configuration.
- Destructive operations require the same authorization as equivalent manual operations.
- Tool output is evidence only when it corresponds to the current revision and intended environment.
- A tool failure is reported as FAIL/BLOCKED/NOT RUN, never silently converted to PASS.
- Agents must distinguish source-of-truth data from convenience tooling.
- Prefer bounded high-level domain operations over a broad raw low-level agent API.
- SaaS/editor state without a deterministic repository return path is convenience/research, not authoritative project state.
- Dev/editor/proof tooling stays outside shipping artifacts unless explicitly promoted and reviewed.

## MCP configuration

Projects may keep MCP-specific configuration locally, but Gumball should standardize:

- capability names;
- expected purpose;
- trust level;
- whether the tool is required or optional for a profile;
- which operations require explicit human approval;
- how unavailable tooling affects validation.

Do not copy a project's private endpoints, machine paths, tokens or environment-specific MCP configuration into Gumball.

## Upstream rule

When a project discovers a reusable tool workflow, promote the general capability contract and safe operating rules. Keep product-specific endpoints and editor/runtime commands downstream.

