# EC2 GitHub repository access

On 25 October 2026, the EC2 office checkout was configured with a repository-scoped SSH deploy key for `amalraj020-a11y/10am-office-work`, with write permission explicitly approved by the owner. The private key stays in the EC2 ubuntu account's `.ssh` directory and is never committed. The repository remote uses SSH and strict GitHub host-key checking.

This enables the EC2 machine to fetch and push this repository while the Windows PC is off. It does not prove the daily business workflow runs end to end. The 10 AM automation remains disabled until its research, build, email and reporting gates pass a full unattended test.
