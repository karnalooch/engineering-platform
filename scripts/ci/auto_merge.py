#!/usr/bin/env python3
"""Fail-closed automatic merge for low-risk engineering-platform pull requests."""

from __future__ import annotations

import json
import os
import re
import sys
from collections.abc import Iterable
from pathlib import PurePosixPath
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

API_ROOT = "https://api.github.com"
GRAPHQL_URL = "https://api.github.com/graphql"

ELIGIBLE_MARKER = re.compile(r"(?mi)^\s*Auto-merge:\s*eligible\s*$")
MANUAL_MARKER = re.compile(r"(?mi)^\s*Auto-merge:\s*manual\s*$")

REQUIRED_CHECKS = (
    "Aggregate CI gate",
    "Governance policy / Governance guard",
)

RISKY_PREFIXES = (
    ".github/",
    "scripts/",
)

RISKY_EXACT = {
    "VERSION",
    "CHANGELOG.md",
    "SECURITY.md",
    ".gitattributes",
    ".gitmodules",
    "LICENSE",
    "LICENSE.md",
    "LICENSE.txt",
    "pyproject.toml",
    "package.json",
    "pnpm-lock.yaml",
    "pnpm-workspace.yaml",
    "package-lock.json",
    "yarn.lock",
    "docs/AGGREGATE_GATE.md",
    "docs/AUTO_MERGE.md",
    "docs/CONTRACT.md",
    "docs/GOVERNANCE_GUARD.md",
    "docs/ROLLOUT.md",
    "docs/VERSIONING.md",
}

RISKY_BASENAMES = {
    ".env",
    ".env.example",
    "Pipfile",
    "Pipfile.lock",
    "poetry.lock",
}

SENSITIVE_SUFFIXES = (
    ".key",
    ".pem",
    ".p12",
    ".pfx",
)

REQUIREMENTS_SUFFIXES = {".txt", ".in"}


class AutomationError(RuntimeError):
    """Raised when the controller cannot make a safe decision."""


class ApiError(AutomationError):
    def __init__(self, status: int, message: str) -> None:
        super().__init__(f"GitHub API {status}: {message}")
        self.status = status


class GitHubApi:
    def __init__(self, token: str) -> None:
        if not token:
            raise AutomationError("GITHUB_TOKEN is required")
        self._token = token

    def _request(
        self,
        method: str,
        url: str,
        payload: dict[str, Any] | None = None,
    ) -> tuple[Any, dict[str, str]]:
        body = None if payload is None else json.dumps(payload).encode("utf-8")
        request = Request(
            url,
            data=body,
            method=method,
            headers={
                "Authorization": f"Bearer {self._token}",
                "Accept": "application/vnd.github+json",
                "Content-Type": "application/json",
                "User-Agent": "engineering-platform-fail-closed-auto-merge",
                "X-GitHub-Api-Version": "2022-11-28",
            },
        )
        try:
            with urlopen(request, timeout=30) as response:
                raw = response.read().decode("utf-8")
                data = json.loads(raw) if raw else None
                headers = {
                    key.lower(): value for key, value in response.headers.items()
                }
                return data, headers
        except HTTPError as exc:
            raw = exc.read().decode("utf-8", errors="replace")
            try:
                parsed = json.loads(raw)
                message = parsed.get("message", exc.reason)
            except json.JSONDecodeError:
                message = exc.reason
            raise ApiError(exc.code, str(message)) from exc
        except URLError as exc:
            raise AutomationError(
                f"GitHub transport error: {exc.reason}"
            ) from exc
        except json.JSONDecodeError as exc:
            raise AutomationError("GitHub returned invalid JSON") from exc

    def rest(
        self,
        method: str,
        path: str,
        payload: dict[str, Any] | None = None,
        *,
        query: dict[str, Any] | None = None,
    ) -> tuple[Any, dict[str, str]]:
        suffix = ""
        if query:
            suffix = "?" + urlencode(query)
        return self._request(method, f"{API_ROOT}{path}{suffix}", payload)

    def graphql(self, query: str, variables: dict[str, Any]) -> dict[str, Any]:
        data, _headers = self._request(
            "POST",
            GRAPHQL_URL,
            {"query": query, "variables": variables},
        )
        if not isinstance(data, dict):
            raise AutomationError("GraphQL response is not an object")
        errors = data.get("errors")
        if errors:
            messages = "; ".join(
                str(error.get("message", "unknown GraphQL error"))
                for error in errors
            )
            raise AutomationError(f"GitHub GraphQL error: {messages}")
        result = data.get("data")
        if not isinstance(result, dict):
            raise AutomationError("GraphQL response is missing data")
        return result


def auto_merge_mode(body: str | None) -> str | None:
    text = body or ""
    if MANUAL_MARKER.search(text):
        return "manual"
    if ELIGIBLE_MARKER.search(text):
        return "eligible"
    return None


def is_risky_path(path: str) -> bool:
    normalized = path.strip().removeprefix("./")
    pure = PurePosixPath(normalized)
    basename = pure.name
    basename_lower = basename.lower()
    lowered = normalized.lower()

    if normalized in RISKY_EXACT:
        return True
    if any(normalized.startswith(prefix) for prefix in RISKY_PREFIXES):
        return True
    if basename in RISKY_BASENAMES:
        return True
    if basename_lower.startswith("requirements") and pure.suffix.lower() in REQUIREMENTS_SUFFIXES:
        return True
    if lowered.endswith(SENSITIVE_SUFFIXES):
        return True
    return False


def risky_paths(paths: Iterable[str]) -> list[str]:
    return sorted(path for path in paths if is_risky_path(path))


def latest_check_conclusions(
    check_runs: Iterable[dict[str, Any]],
) -> dict[str, str | None]:
    latest: dict[str, tuple[int, str | None]] = {}
    for run in check_runs:
        name = str(run.get("name", ""))
        raw_run_id = run.get("id")
        if raw_run_id is None:
            raise AutomationError(f"check run {name!r} is missing id")
        try:
            run_id = int(raw_run_id)
        except (TypeError, ValueError) as exc:
            raise AutomationError(f"check run {name!r} has invalid id") from exc
        conclusion = run.get("conclusion")
        previous = latest.get(name)
        if previous is None or run_id > previous[0]:
            latest[name] = (
                run_id,
                None if conclusion is None else str(conclusion),
            )
    return {name: value[1] for name, value in latest.items()}


def missing_required_checks(
    check_runs: Iterable[dict[str, Any]],
) -> list[str]:
    conclusions = latest_check_conclusions(check_runs)
    return [
        name
        for name in REQUIRED_CHECKS
        if conclusions.get(name) != "success"
    ]


def has_changes_requested(reviews: Iterable[dict[str, Any]]) -> bool:
    latest_by_reviewer: dict[str, tuple[int, str]] = {}
    for review in reviews:
        user = review.get("user") or {}
        login = str(user.get("login", ""))
        if not login:
            continue
        raw_id = review.get("id", 0)
        try:
            review_id = int(raw_id)
        except (TypeError, ValueError) as exc:
            raise AutomationError(
                f"review from {login!r} has invalid id"
            ) from exc
        state = str(review.get("state", "")).upper()
        if state not in {"APPROVED", "CHANGES_REQUESTED"}:
            continue
        previous = latest_by_reviewer.get(login)
        if previous is None or review_id > previous[0]:
            latest_by_reviewer[login] = (review_id, state)
    return any(
        state == "CHANGES_REQUESTED"
        for _review_id, state in latest_by_reviewer.values()
    )


PULL_REQUEST_RELATIONS_QUERY = """
query($owner: String!, $name: String!, $number: Int!) {
  repository(owner: $owner, name: $name) {
    pullRequest(number: $number) {
      reviewThreads(first: 100) {
        pageInfo { hasNextPage }
        nodes { isResolved }
      }
      closingIssuesReferences(first: 100) {
        pageInfo { hasNextPage }
        nodes {
          number
          repository { nameWithOwner }
        }
      }
    }
  }
}
"""


def pull_request_relations(
    api: GitHubApi,
    *,
    owner: str,
    name: str,
    number: int,
    repository: str,
) -> tuple[int, list[int]]:
    data = api.graphql(
        PULL_REQUEST_RELATIONS_QUERY,
        {"owner": owner, "name": name, "number": number},
    )
    repository_data = data.get("repository")
    pull_request = (
        repository_data.get("pullRequest")
        if isinstance(repository_data, dict)
        else None
    )
    if not isinstance(pull_request, dict):
        raise AutomationError(
            f"pull request #{number} could not be resolved"
        )

    threads = pull_request.get("reviewThreads", {})
    if not isinstance(threads, dict):
        raise AutomationError(
            f"pull request #{number} reviewThreads is malformed"
        )
    if threads.get("pageInfo", {}).get("hasNextPage"):
        raise AutomationError(
            f"pull request #{number} has more than 100 review threads; "
            "manual merge required"
        )
    unresolved = sum(
        1
        for node in threads.get("nodes", [])
        if not bool(node.get("isResolved"))
    )

    closing = pull_request.get("closingIssuesReferences", {})
    if not isinstance(closing, dict):
        raise AutomationError(
            f"pull request #{number} closingIssuesReferences is malformed"
        )
    if closing.get("pageInfo", {}).get("hasNextPage"):
        raise AutomationError(
            f"pull request #{number} closes more than 100 issues; "
            "manual merge required"
        )
    issue_numbers = sorted(
        {
            int(node["number"])
            for node in closing.get("nodes", [])
            if node.get("repository", {}).get("nameWithOwner") == repository
        }
    )
    return unresolved, issue_numbers


def list_open_pull_requests(
    api: GitHubApi,
    repository: str,
) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for page in range(1, 6):
        pulls, _headers = api.rest(
            "GET",
            f"/repos/{repository}/pulls",
            query={"state": "open", "per_page": 100, "page": page},
        )
        if not isinstance(pulls, list):
            raise AutomationError(
                "open pull request response is not a list"
            )
        result.extend(pulls)
        if len(pulls) < 100:
            return result
    raise AutomationError(
        "more than 500 open pull requests; refusing incomplete scan"
    )


def list_changed_files(
    api: GitHubApi,
    repository: str,
    number: int,
) -> list[str]:
    result: list[str] = []
    for page in range(1, 6):
        files, _headers = api.rest(
            "GET",
            f"/repos/{repository}/pulls/{number}/files",
            query={"per_page": 100, "page": page},
        )
        if not isinstance(files, list):
            raise AutomationError(
                f"PR #{number} files response is not a list"
            )
        result.extend(str(item["filename"]) for item in files)
        if len(files) < 100:
            return result
    raise AutomationError(
        f"PR #{number} changes more than 500 files; manual merge required"
    )


def list_reviews(
    api: GitHubApi,
    repository: str,
    number: int,
) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for page in range(1, 4):
        reviews, _headers = api.rest(
            "GET",
            f"/repos/{repository}/pulls/{number}/reviews",
            query={"per_page": 100, "page": page},
        )
        if not isinstance(reviews, list):
            raise AutomationError(
                f"PR #{number} reviews response is not a list"
            )
        result.extend(reviews)
        if len(reviews) < 100:
            return result
    raise AutomationError(
        f"PR #{number} has more than 300 reviews; manual merge required"
    )


def list_check_runs(
    api: GitHubApi,
    repository: str,
    sha: str,
) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    expected_total: int | None = None

    for page in range(1, 6):
        payload, _headers = api.rest(
            "GET",
            f"/repos/{repository}/commits/{sha}/check-runs",
            query={"per_page": 100, "page": page},
        )
        if not isinstance(payload, dict):
            raise AutomationError(
                "check-runs response is not an object"
            )
        total = int(payload.get("total_count", 0))
        if expected_total is None:
            expected_total = total
        elif expected_total != total:
            raise AutomationError(
                "check-run total changed during evaluation; retry later"
            )
        runs = payload.get("check_runs", [])
        if not isinstance(runs, list):
            raise AutomationError("check_runs is not a list")
        result.extend(runs)
        if len(result) >= total:
            return result
        if len(runs) < 100:
            break

    raise AutomationError(
        f"{expected_total or 0} check runs reported but only "
        f"{len(result)} retrieved; refusing partial evaluation"
    )


def print_block(number: int, reason: str) -> None:
    print(f"auto-merge: PR #{number} BLOCKED: {reason}")


def evaluate_pull_request(
    api: GitHubApi,
    *,
    repository: str,
    repository_owner: str,
    pr_summary: dict[str, Any],
) -> str:
    number = int(pr_summary["number"])
    if auto_merge_mode(pr_summary.get("body")) != "eligible":
        return "not-eligible"

    pr, _headers = api.rest(
        "GET",
        f"/repos/{repository}/pulls/{number}",
    )
    if not isinstance(pr, dict):
        raise AutomationError(
            f"PR #{number} payload is not an object"
        )

    if auto_merge_mode(pr.get("body")) != "eligible":
        print_block(
            number,
            "eligible marker was removed or manual marker is present",
        )
        return "blocked"
    if pr.get("state") != "open":
        return "not-open"
    if bool(pr.get("draft")):
        print_block(number, "PR is still draft")
        return "blocked"
    if pr.get("base", {}).get("ref") != "main":
        print_block(number, "base branch is not main")
        return "blocked"
    if pr.get("head", {}).get("repo", {}).get("full_name") != repository:
        print_block(number, "head repository is not the protected repository")
        return "blocked"
    if pr.get("user", {}).get("login") != repository_owner:
        print_block(number, "PR author is not repository owner")
        return "blocked"

    base_sha = str(pr.get("base", {}).get("sha", ""))
    if not re.fullmatch(r"[0-9a-f]{40}", base_sha):
        raise AutomationError(
            f"PR #{number} base SHA is missing or invalid"
        )

    paths = list_changed_files(api, repository, number)
    if not paths:
        print_block(number, "PR has no changed files")
        return "blocked"

    risky = risky_paths(paths)
    if risky:
        preview = ", ".join(risky[:8])
        suffix = (
            ""
            if len(risky) <= 8
            else f" (+{len(risky) - 8} more)"
        )
        print_block(
            number,
            f"high-risk paths: {preview}{suffix}",
        )
        return "blocked"

    head_sha = str(pr.get("head", {}).get("sha", ""))
    if not re.fullmatch(r"[0-9a-f]{40}", head_sha):
        raise AutomationError(
            f"PR #{number} head SHA is missing or invalid"
        )

    missing_checks = missing_required_checks(
        list_check_runs(api, repository, head_sha)
    )
    if missing_checks:
        print_block(
            number,
            "required checks not green: " + ", ".join(missing_checks),
        )
        return "blocked"

    reviews = list_reviews(api, repository, number)
    if has_changes_requested(reviews):
        print_block(
            number,
            "latest review contains CHANGES_REQUESTED",
        )
        return "blocked"

    repo_owner, repo_name = repository.split("/", 1)
    unresolved, closing_issues = pull_request_relations(
        api,
        owner=repo_owner,
        name=repo_name,
        number=number,
        repository=repository,
    )
    if unresolved:
        print_block(
            number,
            f"{unresolved} unresolved review thread(s)",
        )
        return "blocked"
    if not closing_issues:
        print_block(
            number,
            "no same-repository closing Issue is linked",
        )
        return "blocked"

    mergeable = pr.get("mergeable")
    mergeable_state = str(pr.get("mergeable_state", "unknown"))
    if mergeable is not True:
        print_block(
            number,
            f"GitHub mergeable={mergeable!r}",
        )
        return "blocked"

    if mergeable_state == "behind":
        api.rest(
            "PUT",
            f"/repos/{repository}/pulls/{number}/update-branch",
            {"expected_head_sha": head_sha},
        )
        print(
            f"auto-merge: PR #{number} UPDATED from main; "
            "waiting for fresh checks"
        )
        return "updated"

    if mergeable_state != "clean":
        print_block(
            number,
            f"mergeable_state={mergeable_state!r}, expected 'clean'",
        )
        return "blocked"

    # Re-read every mutable safety signal immediately before the write.
    # The merge API also receives the exact reviewed head SHA, so a
    # synchronize race after this snapshot is rejected server-side.
    latest_pr, _headers = api.rest(
        "GET",
        f"/repos/{repository}/pulls/{number}",
    )
    if not isinstance(latest_pr, dict):
        raise AutomationError(
            f"PR #{number} final payload is not an object"
        )

    if auto_merge_mode(latest_pr.get("body")) != "eligible":
        print_block(
            number,
            "merge marker changed during evaluation",
        )
        return "blocked"
    if latest_pr.get("state") != "open" or bool(latest_pr.get("draft")):
        print_block(
            number,
            "PR state changed during evaluation",
        )
        return "blocked"
    if latest_pr.get("base", {}).get("ref") != "main":
        print_block(
            number,
            "base branch changed during evaluation",
        )
        return "blocked"
    if latest_pr.get("head", {}).get("repo", {}).get("full_name") != repository:
        print_block(
            number,
            "head repository changed during evaluation",
        )
        return "blocked"
    if latest_pr.get("user", {}).get("login") != repository_owner:
        print_block(
            number,
            "PR author changed during evaluation",
        )
        return "blocked"

    latest_head_sha = str(
        latest_pr.get("head", {}).get("sha", "")
    )
    latest_base_sha = str(
        latest_pr.get("base", {}).get("sha", "")
    )
    if latest_head_sha != head_sha or latest_base_sha != base_sha:
        print_block(
            number,
            "head/base snapshot changed during evaluation",
        )
        return "blocked"

    final_missing_checks = missing_required_checks(
        list_check_runs(api, repository, head_sha)
    )
    if final_missing_checks:
        print_block(
            number,
            "required checks changed before merge: "
            + ", ".join(final_missing_checks),
        )
        return "blocked"

    if has_changes_requested(
        list_reviews(api, repository, number)
    ):
        print_block(
            number,
            "review state changed to CHANGES_REQUESTED before merge",
        )
        return "blocked"

    final_unresolved, final_closing_issues = pull_request_relations(
        api,
        owner=repo_owner,
        name=repo_name,
        number=number,
        repository=repository,
    )
    if final_unresolved:
        print_block(
            number,
            f"{final_unresolved} unresolved review thread(s) before merge",
        )
        return "blocked"
    if final_closing_issues != closing_issues:
        print_block(
            number,
            "closing Issue set changed during evaluation",
        )
        return "blocked"

    if latest_pr.get("mergeable") is not True:
        print_block(
            number,
            f"final GitHub mergeable={latest_pr.get('mergeable')!r}",
        )
        return "blocked"
    final_mergeable_state = str(
        latest_pr.get("mergeable_state", "unknown")
    )
    if final_mergeable_state != "clean":
        print_block(
            number,
            "final mergeable_state="
            f"{final_mergeable_state!r}, expected 'clean'",
        )
        return "blocked"

    result, _headers = api.rest(
        "PUT",
        f"/repos/{repository}/pulls/{number}/merge",
        {
            "sha": head_sha,
            "merge_method": "squash",
            "commit_title": (
                f"{latest_pr.get('title', '').strip()} (#{number})"
            ),
        },
    )
    if not isinstance(result, dict) or not bool(result.get("merged")):
        message = (
            result.get("message", "merge rejected")
            if isinstance(result, dict)
            else "merge rejected"
        )
        raise AutomationError(
            f"PR #{number} merge was rejected: {message}"
        )

    print(f"auto-merge: PR #{number} MERGED via squash")

    for issue_number in closing_issues:
        issue, _headers = api.rest(
            "PATCH",
            f"/repos/{repository}/issues/{issue_number}",
            {"state": "closed", "state_reason": "completed"},
        )
        if (
            not isinstance(issue, dict)
            or issue.get("state") != "closed"
            or issue.get("state_reason") != "completed"
        ):
            raise AutomationError(
                f"PR #{number} merged but Issue #{issue_number} "
                "did not close as completed"
            )
        print(
            f"auto-merge: issue #{issue_number} CLOSED as completed"
        )

    return "merged"


def evaluate_eligible_pull_requests(
    api: GitHubApi,
    *,
    repository: str,
    repository_owner: str,
    pull_requests: Iterable[dict[str, Any]],
) -> int:
    had_errors = False
    for pr in pull_requests:
        number = pr.get("number", "?")
        try:
            evaluate_pull_request(
                api,
                repository=repository,
                repository_owner=repository_owner,
                pr_summary=pr,
            )
        except (
            AutomationError,
            KeyError,
            TypeError,
            ValueError,
        ) as exc:
            print(
                f"auto-merge: PR #{number} FAIL: {exc}",
                file=sys.stderr,
            )
            had_errors = True
    return 1 if had_errors else 0


def main() -> int:
    try:
        repository = os.environ.get("GITHUB_REPOSITORY", "")
        repository_owner = os.environ.get(
            "REPOSITORY_OWNER",
            "",
        )
        token = os.environ.get("GITHUB_TOKEN", "")

        if "/" not in repository:
            raise AutomationError(
                "GITHUB_REPOSITORY must be owner/name"
            )
        if not repository_owner:
            raise AutomationError(
                "REPOSITORY_OWNER is required"
            )

        api = GitHubApi(token)
        pulls = list_open_pull_requests(api, repository)
        eligible = [
            pr
            for pr in pulls
            if auto_merge_mode(pr.get("body")) == "eligible"
        ]
        print(
            f"auto-merge: evaluating {len(eligible)} "
            "eligible open PR(s)"
        )
        return evaluate_eligible_pull_requests(
            api,
            repository=repository,
            repository_owner=repository_owner,
            pull_requests=eligible,
        )
    except (
        AutomationError,
        KeyError,
        TypeError,
        ValueError,
    ) as exc:
        print(f"auto-merge: FAIL: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
