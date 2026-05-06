# agentic-writer + linkedin-content-cicd

A Claude Code plugin and CI/CD pipeline for generating and automatically publishing LinkedIn posts, with a Medium article ad-hoc generator for long-form content and continous delivery since medium does not have an API for continous deployment. Targets technical professionals in ML, AI Engineering, and Fullstack Software Engineering.

![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)
![Claude Code Plugin](https://img.shields.io/badge/Claude_Code-Plugin-blue.svg)

## Features

- **LinkedIn Post Generator** (`/linkedin`) -- Algorithm-optimized posts with enforced character limits (1,000-1,300 optimal, 3,000 max), text-only formatting, and engagement best practices
- **Medium Article Generator** (`/medium`) -- SEO-optimized technical articles (1,600-2,000 words, 7-minute read) with markdown formatting, keyword placement, and tag suggestions. Medium has no publishing API, so the `medium/` folder is intentionally flat for manual copy-paste onto the platform. Subfolder structure (`drafts/`, `validated/`, `posted/`) serves as an archive of the content lifecycle
- **Automated LinkedIn Publishing** -- GitHub Actions cron job posts from a queue on weekdays at 11 PM UTC (3 PM PST); to compensate for deployment lag aiming for 11 PM UTC (4 PM PST) live to production, with dry run support and automatic content shuffle & recycling
- **Writing Style Enforcement** -- 127 banned words, active voice only, spartan conversational tone, no emojis or hashtags
- **Token Lifecycle Management** -- Weekly expiry checks with gmail reminders and auto-created GitHub issues before the 60-day OAuth token expires

## Installation

### As a Plugin (Recommended)

```bash
claude plugins install github:thomas-to-bcheme/agentic-writer
```

### For Development

```bash
git clone https://github.com/thomas-to-bcheme/agentic-writer.git
cd agentic-writer
```

### Prerequisites

- [Claude Code CLI](https://claude.ai/code) installed and configured
- Git
- A LinkedIn Developer App with the `w_member_social` permission scope (for automated posting)
- An OAuth2 access token stored as `LINKEDIN_ACCESS_TOKEN` in GitHub Actions secrets

No build, test, or lint commands. This is a prompt-template project with a Python posting script and GitHub Actions workflows.

## Usage

### Generate a LinkedIn Post

```
/linkedin Building a real-time ML inference pipeline with 50ms latency
```

Output: Plain text post saved to `linkedin/drafts/YYYY-MM-DD-topic.md`

### Generate a Medium Article

```
/medium Optimizing transformer model serving costs in production
```

Output: Markdown article saved to `medium/drafts/YYYY-MM-DD-topic.md`

## Content Workflow

```
Draft (drafts/) --> Review --> Validate (not-posted/) --> Auto-Post --> Archive (posted/)
                                                                           |
                                                      Recycle when empty <-+
```

1. **Draft** -- Skill generates content in `linkedin/drafts/` with YAML frontmatter (date, topic, target audience)
2. **Review** -- Validate against writing rules and add personal touches
3. **Stage** -- Move approved content to `linkedin/not-posted/` to enter the posting queue
4. **Auto-Post** -- GitHub Actions reads the next slug from `.post-queue`, posts via the LinkedIn API, and moves the file to `posted/`
5. **Recycle** -- When `not-posted/` is empty, all `posted/` files are recycled back in randomized order

### Post Queue

The file `linkedin/.post-queue` maintains the publication order. Topics are listed one per line as kebab-case slugs matching filenames in `not-posted/`. The automated pipeline reads from the top and advances after each post.

### Dry Run

Set `DRY_RUN=true` when triggering the workflow manually. This posts with `CONNECTIONS` visibility (only your network sees it) and does not modify the queue or move files.

### Manual Trigger

Go to Actions > Post to LinkedIn > Run workflow. Select `dry_run: true` to test without publishing publicly.

## Project Structure

```
skills/linkedin/SKILL.md              # LinkedIn post generator skill
skills/medium/SKILL.md                # Medium article generator skill
scripts/post-to-linkedin.py           # Automated posting script
linkedin/                             # LinkedIn content lifecycle
  drafts/                             #   Generated drafts pending review
  not-posted/                         #   Approved content queued for posting
  posted/                             #   Published content archive
  .post-queue                         #   Publication order (one slug per line)
medium/                               # Medium content lifecycle (manual publish, no API)
  drafts/                             #   Generated drafts pending review
  validated/                          #   Approved content ready to copy-paste to Medium
  posted/                             #   Published content archive
.github/workflows/                    # CI/CD automation
  post-to-linkedin.yml                #   Cron: weekdays 11 PM UTC
  token-expiry-check.yml              #   Weekly token expiry reminder
.github/linkedin-token-issued.txt     # Token issuance date (YYYY-MM-DD)
how-to.md                             # LinkedIn API reference (v202604)
CLAUDE.md                             # Claude Code project guidance
```

## Writing Constraints

Both generators enforce these rules:

- Active voice only, spartan and conversational tone
- No emojis, hashtags, semicolons, or em dashes
- 127 banned words (e.g., "delve", "game-changer", "unlock", "revolutionize")
- No salesy or self-congratulatory language
- Data-driven claims with metrics over vague statements
- Posts open with "Hello World," and close with a standard CTA

**LinkedIn-specific**: Plain text only (no markdown). External links included despite algorithm reach penalty.

**Medium-specific**: Markdown formatting required. SEO keyword placement in title, subtitle, first paragraph, and H2 headings. 5 suggested tags per article. Image placeholders every 300-500 words. Author must personalize before publishing (Medium deprioritizes AI content).

## Setup

### 1. LinkedIn API Authorization

1. Create a [LinkedIn Developer App](https://www.linkedin.com/developers) with the `w_member_social` permission scope
2. Generate an access token at the [OAuth Token Generator](https://www.linkedin.com/developers/tools/oauth/token-generator) -- select scopes `w_member_social`, `openid`, `profile`
3. Add the token as `LINKEDIN_ACCESS_TOKEN` in your repo's **Settings > Secrets and variables > Actions**
4. Get your Person URN (see [how-to.md](how-to.md#setup) for the API call) and add it as `LINKEDIN_PERSON_URN`
5. Set `.github/linkedin-token-issued.txt` to today's date (YYYY-MM-DD) and push

Tokens expire every 60 days. Repeat steps 2-5 to rotate.

### 2. Gmail Notifications (Token Expiry Reminders)

The repo runs a weekly check that emails you when 7 days or less remain on your token. This uses Gmail SMTP with a Google App Password.

1. Enable [2-Step Verification](https://myaccount.google.com/security) on your Google account
2. Generate an [App Password](https://myaccount.google.com/apppasswords) (name it "LinkedIn Token Check")
3. Add two secrets in your repo's **Settings > Secrets and variables > Actions**:
   - `GMAIL_ADDRESS` -- your Gmail address (used as both sender and recipient)
   - `GMAIL_APP_PASSWORD` -- the 16-character app password from step 2

See [how-to.md](how-to.md#setup) for the full setup walkthrough and a summary of all required secrets.

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Content Generation | Claude Code plugin system (Claude Sonnet) |
| Automated Posting | Python + GitHub Actions cron |
| API | LinkedIn Marketing API v202604 |
| Config | YAML frontmatter |
| Content | Markdown with YAML metadata |

## API Reference

See [how-to.md](how-to.md) for full LinkedIn API documentation covering text posts, image/video/document uploads, article posts, media reuse, post management, and API constraints.

## License

MIT
