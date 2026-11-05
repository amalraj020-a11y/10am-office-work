# EC2 office worker status — 2026-11-06

Latest verified state: both `amala-office.timer` and `amala-auth-watch.timer`
were active on EC2 on November 4. The October 29 installation succeeded;
the hourly watcher currently checks model OAuth, not Gmail authorization.
Repository records show website/email runs through November 1. Runs on
November 2–5 stopped before building because Gmail refresh returned
`invalid_grant` and the installed WhatsApp adapter could not verify a new
recipient's registration. The November 5 EC2 result confirms that blocker.
Gmail reauthorization and a fresh approved live test remain pending.

The October 29 owner WhatsApp report returned a gateway timeout after the
request was submitted. Delivery is unknown; do not resend that report blindly.
The runner now uses the Gateway `send` RPC with a 60-second budget and a stable
idempotency key, so a retry cannot duplicate a report whose first result is
uncertain. This repair still requires deployment and an EC2 verification.
Temporary maintenance SSH ingress is removed after each connection.

## Earlier setup evidence

The `amala-office.timer` systemd user timer is enabled on EC2 for 10:00 AM
Asia/Kolkata every day. On 2026-10-28, systemd reported its next trigger as
2026-10-29 10:00:00 IST. User linger is enabled and the OpenClaw gateway was
active. The older OpenClaw cron remains disabled to prevent duplicate runs.

The daily runner launches the dedicated OpenClaw `amala-office` agent and
checks its result. The active model route is `openai/gpt-6-astra` through the
user-approved ChatGPT OAuth profile. Groq Qwen did not perform the verified
business run. No OpenAI API key or API billing was configured for this route.

The manual rehearsal selected Bake me mine in Plymouth, Minnesota, and
published a business-specific site using the free ThemeWagon Creative template.
GitHub Pages served the site and two current desktop/mobile screenshots.
Gmail accepted an email to its public business address with both screenshots
attached; the accepted Gmail message ID is recorded in
`work/bake-me-mine-plymouth/run.json`. Delivery to the inbox is unverified.
The business phone was found, but the exposed WhatsApp resolver could not
confirm registration, so no WhatsApp message was sent to that business.

The OpenClaw agent encountered a model/gateway error after the email send.
The known receipt was manually reconciled without sending again; the updated
run record and Excel tracker were pushed. The runner now has a conservative
post-send recovery path that publishes only a matching, already-sent receipt
with verified site and model evidence. That recovery path compiled and its
model-evidence check passed, but it has not been exercised in another live
post-send failure. The next scheduled run remains the first unattended test.

The workflow depends on the EC2 instance remaining running, available AWS
credits, GitHub Pages, connected Gmail/WhatsApp sessions, public lead data,
and model availability. A daily success or six months of zero charges is not
guaranteed. Check `work/` and the private EC2 run result after each run; do
not retry any outreach whose send receipt is unknown.

An hourly EC2 auth watcher was installed and verified active on October 29.
It inspects the
office OpenAI OAuth profile without model tokens while healthy. If unavailable,
it attempts a small live refresh check, then tries one WhatsApp alert per India
calendar day. Alert delivery requires the separate Amala WhatsApp session to
remain connected. Its last verified healthy model check on October 29 does
not establish current Gmail health or prove WhatsApp alert delivery.
