# 10 AM Office Work

> **Current EC2 setup:** See [cloud/README.md](cloud/README.md) and
> [cloud/RULEBOOK.md](cloud/RULEBOOK.md). The EC2 10 AM job is paused after
> unsuccessful full-workflow tests on 25 October 2026. WhatsApp registration
> verification and an email adapter are not available yet. The Windows
> instructions below describe the
> historical prototype, not a working cloud schedule. Server setup/repair by Codex
> is authorized; scheduled business work must run through OpenClaw and local Qwen.

**25 October one-off preview:** [Nerdvana Bookstore & Cafe](https://amalraj020-a11y.github.io/10am-office-work/websites/nerdvana-bookstore-cafe/) is live with [desktop and mobile screenshots](work/nerdvana-bookstore-cafe/README.md). Qwen chose the prospect and template and wrote copy and an email draft through OpenClaw; Codex assembled and verified the page. The email was not sent because OpenClaw has no connected mail adapter. This test excluded WhatsApp and Excel. The daily job is still disabled.

Amala's 10:00–11:00 AM local-business website workflow, powered by local Ollama `qwen3:4b`.

## Goal

Find local businesses with no functioning official website, create a polished demo using free tools, and offer it for sale without upfront spend.

## Automatic 10 AM workflow

The Windows scheduled task runs `scripts/run-ollama-10am.ps1` every day at 10:00 AM IST. The local Qwen workflow is responsible for:

1. Searching worldwide for a verified local business and checking for a dedicated official website.
2. Generating an original demo website from verified facts only.
3. Testing and saving the website under `sites/<business>/`.
4. Creating the research note, email draft, WhatsApp draft, public screenshot links, and outreach record.
5. Updating `tracker/`, `work/`, and the Excel tracker.
6. Committing and pushing the complete run to this GitHub repository.
7. Sending outreach through the connected channel when available without asking for per-run permission, then recording the exact result for the owner.
8. If WhatsApp is unavailable, recording the reason and moving to another same-niche business with no official website instead of stopping the run.

Qwen does not invent business facts, prices, reviews, or services. Production deployment, payment collection, ownership transfer, and backend work happen only after owner approval and payment agreement. Routine website creation, GitHub/Excel updates, and outreach sending are authorized for the 10 AM workflow without a new permission request each day. This includes every fresh daily test: after validation, Amala sends the prepared outreach through each verified connected channel automatically and reports the exact result afterward.

Codex is prohibited from running, sending, or orchestrating this workflow. OpenClaw must be the only runtime and sender; the local Windows Ollama task is called by OpenClaw. If OpenClaw is unavailable, the run must stop and report `openclaw_not_connected` rather than falling back to Codex.

## Execution ownership

Qwen `qwen3:4b` generates the website copy and outreach message. OpenClaw performs GitHub, email, and WhatsApp actions and reports the exact result. Codex must not perform any project action, including sending, browser control, orchestration, or fallback execution.

## Operating rules

- Work only during the 10:00–11:00 AM IST window.
- Prefer free research, free development tools, GitHub, and free hosting tiers.
- Record evidence before marking a business as having no website.
- Contact-channel priority: record every reliable public phone, WhatsApp number, email, contact form, or social-message channel found, preserve its source URL, and use the available channel for outreach.
- Contact validation before build: verify that each discovered phone/WhatsApp number is correctly formatted and usable through the connected adapter, and verify that each email address is syntactically valid and accepted by the mail adapter before starting website creation.
- Phone-only fallback: when a shop has only a phone number, check that exact number on WhatsApp before building. If WhatsApp is active, continue with the build and WhatsApp outreach. If it is not active, do not build or contact that shop; record the result and continue from step 5 with another same-niche business that has no official website.
- Template selection: strictly choose a polished, reputable free template from the approved sources—especially ThemeWagon or a clearly licensed GitHub repository—and record the exact template URL, repository, and license note before adapting it.
- Template prohibition: never use the workflow's old custom/original layout, never silently fall back to an invented template, and never use a template when its source, license, attribution, or export rights cannot be verified. If validation fails, stop the build and report it.
- Fresh-template rule: do not reuse Foodee, Feane, or any template already recorded for another prospect; select a new template from ThemeWagon's free catalog and record it before building.
- Delivery sequence: deploy the finished demo to GitHub Pages, verify the live URL, capture clean current screenshots, then attach the GitHub Pages live link—not only the repository folder link—to every email and WhatsApp message when available; record every result in the tracker.
- Outreach order: attempt public email, then WhatsApp, then phone call or SMS when the corresponding connected adapter is available; record each attempt and its exact result without claiming success unless visibly confirmed.
- Pre-send checklist: before any email or WhatsApp send, verify (1) the business has no functioning official website, (2) the contact channel is valid, (3) the website shows the correct business name and verified details, (4) `Developed by MultiMax` is visible, (5) template/demo branding and placeholder text are removed, (6) the GitHub Pages URL returns successfully, and (7) the message contains the current live link and GitHub source link. If any check fails, fix it before sending.
- Automatic send rule: after the pre-send checklist passes, OpenClaw sends the prepared message without asking the owner for permission before sending. Only after sending, the report must state the exact channel result—sent, delivered, bounced, failed, or unavailable—and include the live URL and repository record.
- Test demos on mobile and desktop.
- Ask the user to handle or approve payment collection.
- Never claim a message was sent unless the channel visibly reports sent/delivered.
- If a prospect has no usable WhatsApp channel, mark it clearly, ask the owner for a verified contact channel when required, and continue with another same-niche no-website prospect.
- Prospect discovery is global: if the local queue is empty, search other cities and countries for the same niche rather than reporting that there is no work.
- Before delivery, remove template/demo branding such as template names, years, “Free HTML5,” and original demo credits from the customer-facing footer; keep required legal attribution only in the project documentation/license record, and show `Developed by MultiMax`.
- Every outreach message must introduce Amala from MultiMax, explain that MultiMax creates affordable websites for local businesses, mention that the shop had no dedicated website, and say that the work can proceed at a low agreed budget.
- Standard introduction for every 10 AM outreach: “Hi, I’m Amala from MultiMax. MultiMax is a small web development company that creates affordable websites for local businesses. We found your shop and thought it looked great, but noticed it did not have a dedicated website, so we prepared a website concept for you. If you are interested, we can proceed and offer it at a low agreed budget. Tell me and I will send the website preview and full details.”
- Use public direct screenshot URLs when the GitHub repository is not accessible to the recipient.
- Deploy or transfer ownership only after acceptance and payment confirmation.

## Repository contents

- `docs/` — workflow notes and pricing guidance.
- `messages/` — outreach and follow-up templates.
- `tracker/` — spreadsheet/tracker export when the live workbook is available.
- `sites/` — demo websites for qualified prospects.
- `websites/` — website builds organized by business slug.
- `work/` — company-by-company work log, screenshots, README, and Excel tracker.
- `outreach/` — Qwen-generated channel drafts, links, attachments, and delivery status.

## Current example

`Mrs. Wilson's Cafe` has a Qwen-generated demo, two screenshots, a work log, an Excel tracker, and corrected WhatsApp outreach using public direct image URLs. The corrected message was delivered on 2026-10-20.

This repository is a review demo; outreach uses verified public contact channels and the 10 AM workflow reports the exact delivery result afterward. Production delivery and paid work still require owner acceptance.
