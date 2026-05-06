# agentic-writer

A Claude Code plugin for generating professional LinkedIn posts and Medium articles targeting technical professionals in ML, AI Engineering, and Fullstack Software Engineering.

![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)
![Claude Code Plugin](https://img.shields.io/badge/Claude_Code-Plugin-blue.svg)

## Features

- **LinkedIn Post Generator** (`/linkedin`) -- Algorithm-optimized posts with enforced character limits (1,000-1,300 optimal, 3,000 max), text-only formatting, and engagement best practices
- **Medium Article Generator** (`/medium`) -- SEO-optimized technical articles (1,600-2,000 words, 7-minute read) with markdown formatting, keyword placement, and tag suggestions
- **Writing Style Enforcement** -- 127 banned words, active voice only, spartan conversational tone, no emojis or hashtags
- **Content Lifecycle Management** -- Directory-based workflow from draft to validation to publication with a manual post queue for scheduling

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

No additional runtime dependencies. This is a prompt-template project with no build, test, or lint commands.

## Usage

### Generate a LinkedIn Post

```
/linkedin Building a real-time ML inference pipeline with 50ms latency
```

Output: Plain text post saved to `genAI/linkedin/drafts/YYYY-MM-DD-topic.md`

### Generate a Medium Article

```
/medium Optimizing transformer model serving costs in production
```

Output: Markdown article saved to `genAI/medium/drafts/YYYY-MM-DD-topic.md`

## Content Workflow

```
Draft (drafts/) --> Review --> Validate (validated/) --> Publish --> Archive (posted/)
                                                              \--> Reject (not-posted/)
```

1. **Draft** -- Skill generates content in `genAI/<platform>/drafts/` with YAML frontmatter (date, topic, target audience)
2. **Review** -- Validate against writing rules and add personal touches. For Medium, author personalization is critical since the platform deprioritizes AI-generated content
3. **Validate** -- Move approved content to `validated/`
4. **Publish** -- Post to LinkedIn or Medium
5. **Archive** -- Move to `posted/` after publication, or `not-posted/` if rejected

### Post Queue

The file `genAI/linkedin/.post-queue` maintains a list of validated topics in publication order. This serves as a manual scheduling mechanism without requiring external tools like Buffer or Later. Topics are listed one per line as kebab-case slugs matching filenames in `validated/`.

## Project Structure

```
skills/linkedin/SKILL.md              # LinkedIn post generator skill
skills/medium/SKILL.md                # Medium article generator skill
genAI/linkedin/                       # LinkedIn content lifecycle
  drafts/                             #   Generated drafts pending review
  validated/                          #   Approved content ready to publish
  posted/                             #   Published content archive
  not-posted/                         #   Rejected content
  .post-queue                         #   Publication order queue
genAI/medium/                         # Medium content lifecycle
  drafts/                             #   Generated drafts pending review
  validated/                          #   Approved content ready to publish
  posted/                             #   Published content archive
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

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Framework | Claude Code plugin system |
| AI Model | Claude Sonnet |
| Config | YAML frontmatter |
| Content | Markdown with YAML metadata |

## License

MIT
