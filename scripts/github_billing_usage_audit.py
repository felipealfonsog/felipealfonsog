#!/usr/bin/env python3

from __future__ import annotations

import argparse
import calendar
import csv
import json
import os
import sys
import time
from collections import defaultdict
from pathlib import Path
from typing import Any
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError


API = "https://api.github.com"
API_VERSION = "2026-03-10"


def gh_get(path: str, token: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    url = f"{API}{path}"
    if params:
        url += "?" + urlencode(params)

    req = Request(url)
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("X-GitHub-Api-Version", API_VERSION)

    try:
        with urlopen(req, timeout=45) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"GitHub API error {e.code} for {url}\n{body}") from e
    except URLError as e:
        raise RuntimeError(f"Network error for {url}: {e}") from e


def money(value: Any) -> float:
    try:
        return float(value or 0)
    except Exception:
        return 0.0


def write_json(path: Path, data: Any) -> None:
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def write_usage_csv(path: Path, items: list[dict[str, Any]]) -> None:
    fields = [
        "date",
        "product",
        "sku",
        "repositoryName",
        "quantity",
        "unitType",
        "pricePerUnit",
        "grossAmount",
        "discountAmount",
        "netAmount",
    ]

    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for item in items:
            writer.writerow(item)


def write_summary_csv(path: Path, items: list[dict[str, Any]]) -> None:
    fields = [
        "product",
        "sku",
        "unitType",
        "pricePerUnit",
        "grossQuantity",
        "grossAmount",
        "discountQuantity",
        "discountAmount",
        "netQuantity",
        "netAmount",
    ]

    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for item in items:
            writer.writerow(item)


def build_markdown(
    out: Path,
    username: str,
    repository: str,
    year: int,
    month: int,
    usage_items: list[dict[str, Any]],
    summary_items: list[dict[str, Any]],
) -> None:
    gross_total = sum(money(i.get("grossAmount")) for i in usage_items)
    discount_total = sum(money(i.get("discountAmount")) for i in usage_items)
    net_total = sum(money(i.get("netAmount")) for i in usage_items)

    by_repo = defaultdict(lambda: {"gross": 0.0, "discount": 0.0, "net": 0.0})
    by_product = defaultdict(lambda: {"gross": 0.0, "discount": 0.0, "net": 0.0})
    by_sku = defaultdict(lambda: {"gross": 0.0, "discount": 0.0, "net": 0.0})
    by_day = defaultdict(lambda: {"gross": 0.0, "discount": 0.0, "net": 0.0})

    for item in usage_items:
        repo = item.get("repositoryName") or "(no repository)"
        product = item.get("product") or "(unknown product)"
        sku = item.get("sku") or "(unknown sku)"
        day = item.get("date") or "(unknown date)"

        g = money(item.get("grossAmount"))
        d = money(item.get("discountAmount"))
        n = money(item.get("netAmount"))

        for bucket, key in [
            (by_repo, repo),
            (by_product, product),
            (by_sku, sku),
            (by_day, day),
        ]:
            bucket[key]["gross"] += g
            bucket[key]["discount"] += d
            bucket[key]["net"] += n

    def table(title: str, data: dict[str, dict[str, float]]) -> list[str]:
        lines = [f"## {title}", "", "| Name | Gross | Discount | Net/Billed |", "|---|---:|---:|---:|"]
        for name, v in sorted(data.items(), key=lambda kv: kv[1]["gross"], reverse=True):
            lines.append(f"| {name} | ${v['gross']:.2f} | ${v['discount']:.2f} | ${v['net']:.2f} |")
        lines.append("")
        return lines

    md = []
    md.append(f"# GitHub Billing Usage Audit — `{username}`")
    md.append("")
    md.append(f"Period: **{year}-{month:02d}**")
    md.append(f"Repository filter: **{repository}**")
    md.append("")
    md.append("## Executive conclusion")
    md.append("")
    md.append(f"- Gross usage: **${gross_total:.2f}**")
    md.append(f"- Discount / included usage: **${discount_total:.2f}**")
    md.append(f"- Net / billed usage: **${net_total:.2f}**")
    md.append("")
    if net_total == 0:
        md.append("✅ **Net/Billed usage is $0.00. This report does not show debt for this usage.**")
    else:
        md.append("⚠️ **Net/Billed usage is not zero. Review this carefully in GitHub Billing.**")
    md.append("")

    md.extend(table("Usage by repository", by_repo))
    md.extend(table("Usage by product", by_product))
    md.extend(table("Usage by SKU", by_sku))
    md.extend(table("Usage by day", by_day))

    md.append("## Monthly summary endpoint")
    md.append("")
    md.append("| Product | SKU | Gross qty | Gross | Discount | Net/Billed |")
    md.append("|---|---|---:|---:|---:|---:|")
    for item in summary_items:
        md.append(
            f"| {item.get('product','')} | {item.get('sku','')} | "
            f"{money(item.get('grossQuantity')):.2f} | "
            f"${money(item.get('grossAmount')):.2f} | "
            f"${money(item.get('discountAmount')):.2f} | "
            f"${money(item.get('netAmount')):.2f} |"
        )
    md.append("")

    out.write_text("\n".join(md), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--username", required=True)
    parser.add_argument("--repository", required=True, help="owner/repo")
    parser.add_argument("--year", required=True, type=int)
    parser.add_argument("--month", required=True, type=int)
    parser.add_argument("--out-dir", default="billing-usage-report")
    args = parser.parse_args()

    token = os.environ.get("GH_BILLING_TOKEN")
    if not token:
        print("ERROR: Missing GH_BILLING_TOKEN secret.", file=sys.stderr)
        return 2

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    days = calendar.monthrange(args.year, args.month)[1]
    all_usage_items: list[dict[str, Any]] = []

    print(f"Reading daily billing usage for {args.username}, {args.year}-{args.month:02d}", file=sys.stderr)

    for day in range(1, days + 1):
        data = gh_get(
            f"/users/{args.username}/settings/billing/usage",
            token,
            {"year": args.year, "month": args.month, "day": day},
        )
        write_json(out_dir / f"usage-{args.year}-{args.month:02d}-{day:02d}.json", data)

        for item in data.get("usageItems", []):
            all_usage_items.append(item)

        time.sleep(0.2)

    print("Reading monthly summary...", file=sys.stderr)

    summary_all = gh_get(
        f"/users/{args.username}/settings/billing/usage/summary",
        token,
        {"year": args.year, "month": args.month},
    )

    summary_repo = gh_get(
        f"/users/{args.username}/settings/billing/usage/summary",
        token,
        {"year": args.year, "month": args.month, "repository": args.repository},
    )

    write_json(out_dir / "monthly-summary-all.json", summary_all)
    write_json(out_dir / "monthly-summary-repository.json", summary_repo)

    summary_items = summary_repo.get("usageItems", [])

    write_usage_csv(out_dir / "daily-usage.csv", all_usage_items)
    write_summary_csv(out_dir / "monthly-summary-repository.csv", summary_items)

    build_markdown(
        out_dir / "billing-usage-report.md",
        args.username,
        args.repository,
        args.year,
        args.month,
        all_usage_items,
        summary_items,
    )

    print(f"Wrote report to {out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
