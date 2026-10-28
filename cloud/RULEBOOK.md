# EC2 office workflow

This is the authoritative specification for the EC2 10:00–11:00 Asia/Kolkata job.
The EC2 10 AM timer starts OpenClaw; OpenClaw owns the business tools and sending.
The office task uses the dedicated
`amala-office` agent in this repository. The linked WhatsApp account remains `amala`.
The office agent uses `openai/gpt-6-astra` through the user's approved ChatGPT OAuth
profile. Its EC2 model and one benign bash tool call passed on 26 October 2026.
Do not use OpenAI API billing, a paid fallback, or local Ollama on this EC2 host.
The user's subscription has usage limits; a successful model probe is not proof
that the entire office task will fit those limits. Codex installs and repairs the
runtime; the scheduled business work must be performed by OpenClaw. Never claim
the daily job is operational until a full rehearsal passes.

1. The daily timer starts at 10:00 Asia/Kolkata. A Raj-requested manual live test
   may start outside that hour and has its own 55 minute deadline. Use a process
   lock and work on at most one qualified business per run. Never rerun a completed
   prospect or send
   a message again just because a command timed out. Reconcile uncertain sends first.
2. Check the approved OpenAI OAuth route, GitHub authentication, research access, available storage,
   and the actual OpenClaw WhatsApp/email adapters. No Windows PC dependency.
   The separate hourly EC2 auth watcher checks the office model sign-in and
   sends Raj one WhatsApp alert per day if the sign-in cannot be refreshed.
   WhatsApp delivery is possible only while Amala's WhatsApp session is linked.
3. Search worldwide, with no country or city restriction, for a new shop. Check public listings, search results, social
   profiles and linked official sites. Record source URLs and time checked. A missing
   search result alone does not prove that a website does not exist. Skip shops with
   a working official website or an uncertain identity.
4. BEFORE selecting/downloading a template or writing website code, verify at
   least one usable public business contact and record its source, identity match,
   channel and time checked. An email must be visibly associated with that same
   business in a current public source, with a plausible address and a working
   configured sender. A phone number must match the same business; phone syntax
   alone is not WhatsApp
   registration. Before WhatsApp outreach, require an actual connected-adapter lookup
   confirming availability. If WhatsApp is logged out, continue with a verified
   business email when one exists; record the unavailable channel honestly. Email
   syntax and MX records do not prove mailbox delivery; record confidence honestly.
   Use only configured email credentials, never guess them. Do not claim that
   an email is deliverable before its provider accepts it, or that an accepted
   email reached the inbox. If no channel can be verified, do not build; skip
   and research another same-niche shop anywhere in the world.
5. Select a fresh free template from https://themewagon.com/theme-price/free/.
   Record the exact template page, source repository, pinned commit and license.
   Read data/used-templates.json and prior research notes; never reuse a previous
   prospect's template or the retired custom layout. Never silently substitute one.
6. Preserve legally required credits and license notices. If visible attribution
   cannot be removed for free, select a different template. Add `Developed by
   MultiMax`. Replace all demo identity, names, years, fake reviews, fake menu prices,
   contact information and placeholders with verified details or remove the section.
   Do not claim the unsolicited demo is the business's official website.
7. Build under `websites/<unique-business-slug>/`. Check all pages, mobile and desktop,
   links, images, forms and console errors. Do not present nonfunctional ordering,
   payments or database features as working. Use the configured office model for copy and adaptation.
8. Deploy a demo to GitHub Pages in `amalraj020-a11y/10am-office-work`. Verify the
   business-specific live URL contains the right business name and MultiMax footer.
   Do not use a root URL pointing to another shop. Wait for the deployment to succeed.
9. Capture two different clean screenshots of the final live website. Open and
   inspect them, then verify their public URLs and source commit. No old screenshots.
10. Draft clear paragraphs with actual line breaks. Introduce Amala from MultiMax,
    explain that MultiMax builds affordable websites for local businesses, say that
    an independent concept was prepared, include the live preview, source link and
    both screenshots, and invite a reply to discuss a small agreed budget. Mention
    backend/database features only as optional later work. Do not invent credentials
    or promise an exact price. Do not assert website absence more strongly than evidence.
11. After all checks pass, send only through the channel(s) verified in step 4 without
    asking Raj again. Send attachments, not only nonexistent screenshot links.
    Record provider message IDs and precise states: accepted/sent, delivered, bounced,
    failed or unknown. Accepted is not proof of delivered. Respect refusal/opt-out;
    no automatic repeated solicitation. No unsolicited calls or SMS in this workflow.
12. Update `work/<slug>/`, the website README, template-use registry and an Excel
    tracker with public business facts, research sources, license, model, code commit,
    live URL, screenshots, exact outreach text and outcome. Keep credentials, private
    chats, payment details and internal owner contact information out of the public repo.
13. Push the completed records and verify the push. Report to Raj through the existing
    OpenClaw owner channel after the run, including failures. Never claim completion
    without actual artifacts, a verified deployment and send evidence. Owner handles
    payment collection; production transfer and paid extras need a separate agreement.

The historical Windows script and check-in job are not implementations of this flow.
If a required capability fails, record the real blocker and report it; do not silently
fall back to Codex, another model provider, an old template, or a fabricated result.
