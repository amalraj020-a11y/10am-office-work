#!/usr/bin/env python3
"""Zero-cost cloud fallback for the 10 AM/PM local-business website slots."""

from __future__ import annotations

import html
import json
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from openpyxl import Workbook, load_workbook
from playwright.sync_api import sync_playwright


IST = ZoneInfo("Asia/Kolkata")
ROOT = Path(__file__).resolve().parents[1]
CATEGORIES = ("cafe", "restaurant", "bakery")


def slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-") or "business"


def researched_names() -> set[str]:
    names = set()
    for path in (ROOT / "work").glob("*/run.json"):
        try:
            names.add(json.loads(path.read_text(encoding="utf-8"))["business_name"].casefold())
        except (KeyError, ValueError, OSError):
            pass
    return names


def find_candidate(now: datetime):
    used = researched_names()
    seed = now.date().toordinal() + (1 if now.hour >= 16 else 0)
    for attempt in range(8):
        city = (seed + attempt) % 8
        category = CATEGORIES[(seed + attempt) % len(CATEGORIES)]
        result = subprocess.run(
            [sys.executable, str(ROOT / "cloud" / "research_candidates.py"),
             "--city-index", str(city), "--category", category],
            cwd=ROOT, text=True, capture_output=True, timeout=90,
        )
        if result.returncode:
            continue
        payload = json.loads((ROOT / "work" / "research-candidates.json").read_text(encoding="utf-8"))
        candidates = [
            item for item in payload.get("candidates", [])
            if item["business_name"].casefold() not in used
        ]
        candidates.sort(key=lambda item: (not bool(item.get("email_unverified")), item["business_name"]))
        if candidates:
            return candidates[0], payload
    return None, {"note": "No fresh public candidate was available after eight bounded searches."}


def site_html(candidate: dict) -> str:
    name = html.escape(candidate["business_name"])
    city = html.escape(candidate["city"])
    category = html.escape(candidate.get("category") or "local business")
    email = html.escape(candidate.get("email_unverified") or "")
    phone = html.escape(candidate.get("phone_unverified") or "")
    source = html.escape(candidate["source_url"], quote=True)
    contact = " · ".join(part for part in (email, phone) if part) or "Contact details require verification"
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <meta name="description" content="Independent website concept for {name} in {city}.">
  <title>{name} — Independent Website Concept</title>
  <style>
    :root {{ --ink:#17221d; --cream:#fffaf0; --green:#235c46; --gold:#d9a441; }}
    * {{ box-sizing:border-box }} body {{ margin:0; font:16px/1.6 system-ui,sans-serif; color:var(--ink); background:var(--cream) }}
    header {{ min-height:72vh; display:grid; place-items:center; padding:4rem 1.25rem; color:white;
      background:linear-gradient(135deg,#173d30,#2c7558) }}
    .hero {{ max-width:850px; text-align:center }} .eyebrow {{ letter-spacing:.16em; text-transform:uppercase; color:#ffe0a3 }}
    h1 {{ font-size:clamp(2.4rem,8vw,5.6rem); line-height:1; margin:.3em 0 }}
    .button {{ display:inline-block; margin-top:1.2rem; padding:.8rem 1.2rem; border-radius:999px; background:var(--gold); color:#1a1a1a; text-decoration:none; font-weight:700 }}
    main {{ max-width:1000px; margin:auto; padding:4rem 1.25rem }}
    .grid {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(220px,1fr)); gap:1rem }}
    article {{ background:white; border:1px solid #eadfca; border-radius:18px; padding:1.4rem }}
    .notice {{ margin-top:3rem; border-left:5px solid var(--gold); background:#fff3d8; padding:1rem 1.2rem }}
    footer {{ background:#10251d; color:white; padding:2rem 1.25rem; text-align:center }}
    a {{ color:inherit }}
  </style>
</head>
<body>
  <header><div class="hero">
    <div class="eyebrow">{category} · {city}</div>
    <h1>{name}</h1>
    <p>A clean, mobile-friendly concept that helps local customers find essential information quickly.</p>
    <a class="button" href="#contact">View contact details</a>
  </div></header>
  <main>
    <h2>A straightforward local presence</h2>
    <div class="grid">
      <article><h3>Easy to discover</h3><p>A focused home page designed for search, maps and mobile visitors.</p></article>
      <article><h3>Fast on every screen</h3><p>Responsive layout with accessible typography and no heavy framework.</p></article>
      <article><h3>Ready to customize</h3><p>Services, opening hours and genuine photographs can be added after owner confirmation.</p></article>
    </div>
    <section id="contact"><h2>Public contact</h2><p>{contact}</p><p><a href="{source}">Public source record</a></p></section>
    <aside class="notice"><strong>Independent demo:</strong> This concept was prepared by MultiMax and is not an official website. Public facts and contact details must be confirmed by the business before production use.</aside>
  </main>
  <footer>Independent concept for {name}<br><strong>Developed by MultiMax</strong></footer>
</body>
</html>"""


def screenshots(site: Path, site_slug: str):
    output = ROOT / "work" / "screenshots"
    output.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        for label, width, height in (("desktop", 1440, 1000), ("mobile", 390, 844)):
            page = browser.new_page(viewport={"width": width, "height": height})
            page.goto(site.resolve().as_uri(), wait_until="load")
            page.screenshot(path=output / f"{site_slug}-{label}.png", full_page=True)
        browser.close()


def update_workbook(now: datetime, slot: str, candidate: dict | None, status: str, url: str, note: str):
    path = ROOT / "work" / "10-am-office-work-tracker.xlsx"
    if path.exists():
        book = load_workbook(path)
    else:
        book = Workbook()
    sheet = book["Cloud Runs"] if "Cloud Runs" in book.sheetnames else book.create_sheet("Cloud Runs")
    if sheet.max_row == 1 and sheet.cell(1, 1).value is None:
        sheet.append(["Date", "Slot", "Business", "City", "Status", "Preview", "Contact", "Evidence", "Notes"])
    sheet.append([
        now.date().isoformat(), slot,
        candidate["business_name"] if candidate else "",
        candidate["city"] if candidate else "",
        status, url,
        (candidate.get("email_unverified") or candidate.get("phone_unverified") or "") if candidate else "",
        candidate["source_url"] if candidate else "", note,
    ])
    sheet.freeze_panes = "A2"
    sheet.auto_filter.ref = sheet.dimensions
    book.save(path)


def main() -> int:
    now = datetime.now(IST)
    slot = "2200" if now.hour >= 16 or now.hour < 4 else "1000"
    marker_dir = ROOT / "work" / "cloud-runs"
    marker_dir.mkdir(parents=True, exist_ok=True)
    marker = marker_dir / f"{now.date().isoformat()}-{slot}.json"
    if marker.exists():
        print(json.dumps({"status": "skipped_duplicate", "marker": str(marker.relative_to(ROOT))}))
        return 0
    candidate, research = find_candidate(now)
    if candidate is None:
        result = {
            "date": now.date().isoformat(), "slot": slot, "status": "blocked",
            "reason": research["note"], "money_impact": "₹0",
            "credential_access": "none",
        }
        marker.write_text(json.dumps(result, indent=2), encoding="utf-8")
        update_workbook(now, slot, None, "BLOCKED", "", research["note"])
        print(json.dumps(result))
        return 0

    site_slug = slug(candidate["business_name"])
    site_dir = ROOT / "websites" / site_slug
    site_dir.mkdir(parents=True, exist_ok=True)
    index = site_dir / "index.html"
    index.write_text(site_html(candidate), encoding="utf-8")
    rendered = index.read_text(encoding="utf-8")
    required = (
        candidate["business_name"], "Developed by MultiMax", "Independent demo",
        'name="viewport"', candidate["source_url"],
    )
    if not all(item in rendered for item in required):
        raise RuntimeError("Generated website failed deterministic content validation")
    screenshots(index, site_slug)
    live_url = f"https://amalraj020-a11y.github.io/10am-office-work/websites/{site_slug}/"
    run_dir = ROOT / "work" / site_slug
    run_dir.mkdir(parents=True, exist_ok=True)
    note = (
        "Public OpenStreetMap evidence had no website tag, which is not proof that no website exists. "
        "Contact is unverified; outreach remains draft-only until independent identity/contact verification."
    )
    result = {
        "date": now.date().isoformat(), "slot": slot, "status": "complete",
        "business_name": candidate["business_name"], "city": candidate["city"],
        "source": candidate["source_url"], "website_tag_absent": True,
        "contact_status": "needs independent confirmation",
        "outreach_status": "draft_only", "site_path": str(index.relative_to(ROOT)),
        "live_url": live_url, "screenshots": [
            f"work/screenshots/{site_slug}-desktop.png",
            f"work/screenshots/{site_slug}-mobile.png",
        ], "tests": "PASS", "money_impact": "₹0", "credential_access": "none",
        "note": note,
    }
    (run_dir / "run.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    (run_dir / "stage-notes.md").write_text(
        f"# {candidate['business_name']} cloud run\n\n- Slot: {slot}\n- Source: {candidate['source_url']}\n- Preview: {live_url}\n- QA: PASS\n- Outreach: draft only\n\n{note}\n",
        encoding="utf-8",
    )
    contact = candidate.get("email_unverified") or candidate.get("phone_unverified") or "unavailable"
    (run_dir / "outreach.txt").write_text(
        f"DRAFT — DO NOT SEND UNTIL CONTACT IS INDEPENDENTLY VERIFIED\n\n"
        f"Public contact candidate: {contact}\n"
        f"Hello, I’m Amala, Raj’s AI website assistant. We prepared an independent website concept for {candidate['business_name']}. "
        f"If this is the correct business contact and you are interested, the preview is {live_url}\n",
        encoding="utf-8",
    )
    marker.write_text(json.dumps(result, indent=2), encoding="utf-8")
    update_workbook(now, slot, candidate, "COMPLETED", live_url, note)
    print(json.dumps(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
