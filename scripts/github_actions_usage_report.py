#!/usr/bin/env python3
"""
GitHub Actions Usage Audit
Generates a Markdown + CSV report of workflow/job runtime for a repository.

It does NOT read GitHub Billing directly. It estimates usage from Actions runs/jobs.
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import os
import sys
import time
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError


API = "https://api.github.com"


@dataclass
class JobRow:
    run_id: int
    run_number: int | None
    workflow_name: str
    event: str
    branch: str
    run_status: str
    run_conclusion: str
    run_created_at: str
    job_id: int
    job_name: str
    runner_name: str
    runner_group_name: str
    labels: str
    started_at: str
    completed_at: str
    duration_seconds: int
    duration_minutes: float
    html_url: str


def parse_iso(value: str | None) -> dt.datetime | None:
    if not value:
        return None
    return dt.datetime.fromisoformat(value.replace("Z", "+00:00"))


def iso_utc(d: dt.date, end: bool = False) -> str:
    if end:
        t = dt.datetime.combine(d, dt.time.max, tzinfo=dt.timezone.utc)
    else:
        t = dt.datetime.combine(d, dt.time.min, tzinfo=dt.timezone.utc)
    return t.isoformat().replace("+00:00", "Z")


def gh_get(path: str, token: str, params: dict[str, Any] | None = None) -> Any:
    url = f"{API}{path}"
    if params:
        url += "?" + urlencode(params)

    while True:
        req = Request(url)
        req.add_header("Accept", "application/vnd.github+json")
        req.add_header("X-GitHub-Api-Version", "2022-11-28")
        req.add_header("Authorization", f"Bearer {token}")
        try:
            with urlopen(req, timeout=45) as resp:
                remaining = resp.headers.get("X-RateLimit-Remaining")
                if remaining == "0":
                    reset = int(resp.headers.get("X-RateLimit-Reset", "0"))
                    wait = max(1, reset - int(time.time()) + 2)
                    print(f"Rate limit reached. Sleeping {wait}s...", file=sys.stderr)
                    time.sleep(wait)
                    continue
                return json.loads(resp.read().decode("utf-8"))
        except HTTPError as e:
            body = e.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"GitHub API error {e.code} for {url}:\n{body}") from e
        except URLError as e:
            raise RuntimeError(f"Network error for {url}: {e}") from e


def paginate_runs(owner: str, repo: str, token: str, created_filter: str) -> list[dict[str, Any]]:
    all_runs: list[dict[str, Any]] = []
    page = 1
    while True:
        data = gh_get(
            f"/repos/{owner}/{repo}/actions/runs",
            token,
            {
                "per_page": 100,
                "page": page,
                "created": created_filter,
            },
        )
        runs = data.get("workflow_runs", [])
        if not runs:
            break
        all_runs.extend(runs)
        if len(runs) < 100:
            break
        page += 1
    return all_runs


def get_jobs(owner: str, repo: str, token: str, run_id: int) -> list[dict[str, Any]]:
    all_jobs: list[dict[str, Any]] = []
    page = 1
    while True:
        data = gh_get(
            f"/repos/{owner}/{repo}/actions/runs/{run_id}/jobs",
            token,
            {"per_page": 100, "page": page},
        )
        jobs = data.get("jobs", [])
        if not jobs:
            break
        all_jobs.extend(jobs)
        if len(jobs) < 100:
            break
        page += 1
    return all_jobs


def job_duration_seconds(job: dict[str, Any]) -> int:
    started = parse_iso(job.get("started_at"))
    completed = parse_iso(job.get("completed_at"))
    if not started or not completed:
        return 0
    return max(0, int((completed - started).total_seconds()))


def build_rows(owner: str, repo: str, token: str, since: dt.date, until: dt.date) -> list[JobRow]:
    created_filter = f"{iso_utc(since)}..{iso_utc(until, end=True)}"
    runs = paginate_runs(owner, repo, token, created_filter)

    rows: list[JobRow] = []
    print(f"Found {len(runs)} workflow runs in {owner}/{repo} for {since}..{until}", file=sys.stderr)

    for i, run in enumerate(runs, start=1):
        run_id = int(run["id"])
        print(f"[{i}/{len(runs)}] Reading jobs for run {run_id} ({run.get('name')})", file=sys.stderr)
        jobs = get_jobs(owner, repo, token, run_id)

        for job in jobs:
            seconds = job_duration_seconds(job)
            rows.append(
                JobRow(
                    run_id=run_id,
                    run_number=run.get("run_number"),
                    workflow_name=run.get("name") or "(unnamed workflow)",
                    event=run.get("event") or "",
                    branch=run.get("head_branch") or "",
                    run_status=run.get("status") or "",
                    run_conclusion=run.get("conclusion") or "",
                    run_created_at=run.get("created_at") or "",
                    job_id=int(job["id"]),
                    job_name=job.get("name") or "(unnamed job)",
                    runner_name=job.get("runner_name") or "",
                    runner_group_name=job.get("runner_group_name") or "",
                    labels=",".join(job.get("labels") or []),
                    started_at=job.get("started_at") or "",
                    completed_at=job.get("completed_at") or "",
                    duration_seconds=seconds,
                    duration_minutes=round(seconds / 60, 2),
                    html_url=job.get("html_url") or run.get("html_url") or "",
                )
            )
    return rows


def write_csv(rows: list[JobRow], out: Path) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(JobRow.__dataclass_fields__.keys()))
        writer.writeheader()
        for r in rows:
            writer.writerow(r.__dict__)


def pct(part: float, total: float) -> float:
    return round((part / total * 100), 1) if total else 0.0


def write_markdown(rows: list[JobRow], owner: str, repo: str, since: dt.date, until: dt.date, out: Path) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)

    total_seconds = sum(r.duration_seconds for r in rows)
    total_minutes = total_seconds / 60

    by_workflow = defaultdict(lambda: {"jobs": 0, "seconds": 0, "runs": set()})
    by_event = defaultdict(lambda: {"jobs": 0, "seconds": 0})
    by_branch = defaultdict(lambda: {"jobs": 0, "seconds": 0})
    by_day = defaultdict(lambda: {"jobs": 0, "seconds": 0})

    for r in rows:
        by_workflow[r.workflow_name]["jobs"] += 1
        by_workflow[r.workflow_name]["seconds"] += r.duration_seconds
        by_workflow[r.workflow_name]["runs"].add(r.run_id)

        by_event[r.event]["jobs"] += 1
        by_event[r.event]["seconds"] += r.duration_seconds

        by_branch[r.branch or "(no branch)"]["jobs"] += 1
        by_branch[r.branch or "(no branch)"]["seconds"] += r.duration_seconds

        day = (parse_iso(r.run_created_at) or parse_iso(r.started_at))
        by_day[day.date().isoformat() if day else "(unknown)"]["jobs"] += 1
        by_day[day.date().isoformat() if day else "(unknown)"]["seconds"] += r.duration_seconds

    top_jobs = sorted(rows, key=lambda r: r.duration_seconds, reverse=True)[:20]

    def table_summary(title: str, data: dict[str, dict[str, Any]], include_runs: bool = False) -> str:
        lines = [f"## {title}", ""]
        if include_runs:
            lines.append("| Name | Runs | Jobs | Minutes | % |")
            lines.append("|---|---:|---:|---:|---:|")
            items = sorted(data.items(), key=lambda kv: kv[1]["seconds"], reverse=True)
            for name, v in items:
                minutes = v["seconds"] / 60
                lines.append(f"| {name} | {len(v['runs'])} | {v['jobs']} | {minutes:.2f} | {pct(minutes, total_minutes)}% |")
        else:
            lines.append("| Name | Jobs | Minutes | % |")
            lines.append("|---|---:|---:|---:|")
            items = sorted(data.items(), key=lambda kv: kv[1]["seconds"], reverse=True)
            for name, v in items:
                minutes = v["seconds"] / 60
                lines.append(f"| {name} | {v['jobs']} | {minutes:.2f} | {pct(minutes, total_minutes)}% |")
        lines.append("")
        return "\n".join(lines)

    md = []
    md.append(f"# GitHub Actions Usage Audit — `{owner}/{repo}`")
    md.append("")
    md.append(f"Period: **{since} → {until}**")
    md.append("")
    md.append("## Executive summary")
    md.append("")
    md.append(f"- Total jobs analyzed: **{len(rows)}**")
    md.append(f"- Total runtime: **{total_minutes:.2f} minutes**")
    md.append("- This report estimates runtime from workflow jobs. It does **not** read GitHub Billing directly.")
    md.append("- Compare this report with GitHub Billing → Usage → Gross amount / Billed amount.")
    md.append("")
    md.append(table_summary("Usage by workflow", by_workflow, include_runs=True))
    md.append(table_summary("Usage by event", by_event))
    md.append(table_summary("Usage by branch", by_branch))
    md.append(table_summary("Usage by day", by_day))

    md.append("## Top 20 longest jobs")
    md.append("")
    md.append("| Minutes | Workflow | Job | Event | Branch | Conclusion | Link |")
    md.append("|---:|---|---|---|---|---|---|")
    for r in top_jobs:
        md.append(
            f"| {r.duration_minutes:.2f} | {r.workflow_name} | {r.job_name} | {r.event} | "
            f"{r.branch} | {r.run_conclusion} | [job]({r.html_url}) |"
        )
    md.append("")
    md.append("## Practical next checks")
    md.append("")
    md.append("- Look for workflows triggered by `schedule` or too-broad `push` patterns.")
    md.append("- Look for jobs with unnecessary matrix expansion.")
    md.append("- Check artifact/cache retention if storage appears in billing.")
    md.append("- Prefer path filters so documentation/content-only commits do not run heavy jobs.")
    md.append("- Add `concurrency` cancellation to avoid duplicated runs on repeated pushes.")
    md.append("")

    out.write_text("\n".join(md), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit GitHub Actions workflow usage for a repo.")
    parser.add_argument("--repo", required=True, help="owner/repo, for example felipealfonsog/felipealfonsog")
    parser.add_argument("--since", required=True, help="YYYY-MM-DD")
    parser.add_argument("--until", required=True, help="YYYY-MM-DD")
    parser.add_argument("--out-dir", default="usage-report", help="Output directory")
    args = parser.parse_args()

    token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    if not token:
        print("ERROR: set GH_TOKEN or GITHUB_TOKEN.", file=sys.stderr)
        return 2

    if "/" not in args.repo:
        print("ERROR: --repo must be owner/repo", file=sys.stderr)
        return 2

    owner, repo = args.repo.split("/", 1)
    since = dt.date.fromisoformat(args.since)
    until = dt.date.fromisoformat(args.until)

    out_dir = Path(args.out_dir)
    rows = build_rows(owner, repo, token, since, until)

    write_csv(rows, out_dir / "actions-jobs.csv")
    write_markdown(rows, owner, repo, since, until, out_dir / "actions-usage-report.md")

    print(f"Wrote {out_dir / 'actions-usage-report.md'}")
    print(f"Wrote {out_dir / 'actions-jobs.csv'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
