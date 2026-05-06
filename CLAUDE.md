# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**agentic-writer** is a Claude Code plugin for generating professional content. Currently provides a LinkedIn post generator and Medium article generator targeting technical professionals in ML, AI Engineering, and Fullstack Software Engineering.

This is not a compiled software project — there are no build, test, or lint commands. The repository holds prompt templates, agent definitions, and Claude Code configuration.

## Architecture

```
skills/linkedin/SKILL.md                    # LinkedIn post generator (invoke with /linkedin)
skills/medium/SKILL.md                      # Medium article generator (invoke with /medium)
agents/content-reviewer.md                  # Draft review agent (validates posts against rules)
genAI/linkedin/{drafts,validated,posted}/    # LinkedIn post lifecycle
genAI/medium/{drafts,validated,posted}/      # Medium article lifecycle
.claude/settings.json                        # Project permissions
.claude/.mcp.json                            # MCP server configs (placeholder)
.claude/rules/writing-style.md               # Writing rules applied to genAI/**/*.md
.claude-plugin/plugin.json                   # Marketplace plugin manifest
```

- **Skills** (`skills/`) — slash commands with YAML frontmatter (`name`, `description`, `allowed-tools`, `model`). Invoked via `/skill-name`.
- **Agents** (`agents/`) — subagent definitions with tools, model, and system prompts. Spawned automatically or via Agent tool.
- **Rules** (`.claude/rules/`) — path-scoped rules loaded when matching files are accessed.
- **Generated content** saved under `genAI/<platform>/` with subfolders `drafts/`, `validated/`, `posted/`.
- **Workflow**: Draft (`drafts/`) → Review → Validate (`validated/`) → Publish → Archive (`posted/`)

## Plugin Installation

Other users can install this as a Claude Code plugin:
```
claude plugins install github:thomas-to-bcheme/agentic-writer
```

## Key Constraints for LinkedIn Generator

- Posts open with "Hello World," and close with the standard CTA
- 1,000–1,300 characters optimal, 3,000 max
- No emojis, hashtags, subtitles, markdown/asterisks, semicolons, or em dashes in output
- 127 banned words list enforced (see `skills/linkedin/SKILL.md`)
- External links included despite reach penalty (convenience prioritized)
- Active voice only; spartan, conversational tone; never salesy or self-congratulatory

## Key Constraints for Medium Generator

- Articles target 1,600-2,000 words (7-minute read), 2,400 max
- Markdown formatting used (H2/H3 headings, bold, bullet points)
- No emojis, hashtags in body, semicolons, or em dashes
- 127 banned words list enforced (shared with LinkedIn)
- SEO: primary keyword in title, subtitle, first paragraph, and H2s
- 5 suggested tags per article
- Author must personalize before publishing (Medium deprioritizes AI content)
- Active voice only; spartan, conversational tone; never salesy or self-congratulatory
