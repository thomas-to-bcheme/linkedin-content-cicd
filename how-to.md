# How To: LinkedIn API Content Automation

This guide covers the LinkedIn Marketing API (version 202604) as used by this repository. It documents text posting, media workflows (images, videos, documents), content reuse, and the constraints of the API.

## Table of Contents

- [Setup](#setup)
- [Required Headers](#required-headers)
- [How This Repository Posts](#how-this-repository-posts)
- [Workflow: Text-Only Post](#workflow-text-only-post)
- [Workflow: Post with Image](#workflow-post-with-image)
- [Workflow: Post with Video](#workflow-post-with-video)
- [Workflow: Post with Document](#workflow-post-with-document)
- [Workflow: Article Post with Link Preview](#workflow-article-post-with-link-preview)
- [Repurposing Media Across Posts](#repurposing-media-across-posts)
- [Managing Published Posts](#managing-published-posts)
- [Visibility Options](#visibility-options)
- [Mentions and Hashtags](#mentions-and-hashtags)
- [API Constraints and Limitations](#api-constraints-and-limitations)
- [Reference](#reference)

---

## Setup

### LinkedIn API Authorization

1. Create a [LinkedIn Developer App](https://www.linkedin.com/developers) with the `w_member_social` permission scope
2. Go to the [OAuth Token Generator](https://www.linkedin.com/developers/tools/oauth/token-generator)
3. Select your app, check `w_member_social`, `openid`, `profile`
4. Click "Request access token" and copy the token
5. Add the token as `LINKEDIN_ACCESS_TOKEN` in your repo's **Settings > Secrets and variables > Actions**
6. Set `.github/linkedin-token-issued.txt` to today's date (YYYY-MM-DD format) and push the change

Tokens expire every 60 days. Repeat steps 2-6 to rotate. The repo runs a weekly check (`token-expiry-check.yml`) that emails a reminder and creates a GitHub issue when 7 days or less remain.

### Person URN

Your Person URN identifies you as the post author. Obtain it with the Profile API:

```bash
curl -s 'https://api.linkedin.com/v2/userinfo' \
  -H 'Authorization: Bearer {TOKEN}' | jq '.sub'
```

Then construct: `urn:li:person:{sub_value}`

Store this as `LINKEDIN_PERSON_URN` in your GitHub Actions secrets.

### Gmail Email Notifications

The weekly token expiry check sends email reminders via Gmail SMTP. This requires a Google App Password.

**Enable 2-Step Verification** (required for App Passwords):

1. Go to https://myaccount.google.com/security
2. Under "How you sign in to Google", select **2-Step Verification**
3. Follow the prompts to enable it if not already active

**Generate a Google App Password:**

1. Go to https://myaccount.google.com/apppasswords
2. Enter a name (e.g., "LinkedIn Token Check") and click **Create**
3. Copy the 16-character password immediately -- it is only shown once

**Add GitHub Actions secrets** in your repo's **Settings > Secrets and variables > Actions**:

| Secret | Value |
|---|---|
| `GMAIL_ADDRESS` | Your Gmail address (used as both sender and recipient) |
| `GMAIL_APP_PASSWORD` | The 16-character app password from the previous step |

The workflow sends to and from the same address. To send to a different recipient, update the `to:` field in `token-expiry-check.yml`.

### All Required Secrets

| Secret | Purpose |
|---|---|
| `LINKEDIN_ACCESS_TOKEN` | OAuth2 token for the LinkedIn API |
| `LINKEDIN_PERSON_URN` | Your `urn:li:person:{id}` author identifier |
| `GMAIL_ADDRESS` | Gmail address for token expiry notifications |
| `GMAIL_APP_PASSWORD` | Google App Password for SMTP |

---

## Required Headers

Every request to the LinkedIn API must include these headers:

```
Authorization: Bearer {ACCESS_TOKEN}
LinkedIn-Version: 202604
X-Restli-Protocol-Version: 2.0.0
Content-Type: application/json
```

Version 202604 is the latest as of May 2026. Versions are supported for a minimum of one year before sunset.

---

## How This Repository Posts

The automated pipeline in this repository uses `scripts/post-to-linkedin.py` with a GitHub Actions cron schedule (weekdays at 11 PM UTC).

**Flow:**
1. Read the next slug from `linkedin/.post-queue`
2. Read the markdown file from `linkedin/not-posted/{slug}.md`
3. POST the text to the LinkedIn API (text-only, no media)
4. Move the file to `linkedin/posted/`
5. Advance the queue
6. When `not-posted/` is empty, recycle all `posted/` files back in randomized order

**Dry run mode** (`DRY_RUN=true`) posts with `CONNECTIONS` visibility so only your network sees it. The queue and files are not modified.

**Manual trigger:** Go to Actions > Post to LinkedIn > Run workflow. Select `dry_run: true` to test.

---

## Workflow: Text-Only Post

This is what the repository currently uses.

```bash
curl -X POST 'https://api.linkedin.com/rest/posts' \
  -H 'Authorization: Bearer {TOKEN}' \
  -H 'LinkedIn-Version: 202604' \
  -H 'X-Restli-Protocol-Version: 2.0.0' \
  -H 'Content-Type: application/json' \
  --data '{
    "author": "urn:li:person:{id}",
    "commentary": "Your post text here. Max 3000 characters.",
    "visibility": "PUBLIC",
    "distribution": {
      "feedDistribution": "MAIN_FEED",
      "targetEntities": [],
      "thirdPartyDistributionChannels": []
    },
    "lifecycleState": "PUBLISHED",
    "isReshareDisabledByAuthor": false
  }'
```

**Response:** `201 Created` with the post URN in the `x-restli-id` header.

---

## Workflow: Post with Image

Three steps: initialize upload, upload binary, create post.

### Step 1: Initialize Image Upload

```bash
curl -X POST 'https://api.linkedin.com/rest/images?action=initializeUpload' \
  -H 'Authorization: Bearer {TOKEN}' \
  -H 'LinkedIn-Version: 202604' \
  -H 'X-Restli-Protocol-Version: 2.0.0' \
  -H 'Content-Type: application/json' \
  --data '{
    "initializeUploadRequest": {
      "owner": "urn:li:person:{id}"
    }
  }'
```

**Response:**

```json
{
  "value": {
    "uploadUrl": "https://www.linkedin.com/dms-uploads/...",
    "uploadUrlExpiresAt": 1650567510704,
    "image": "urn:li:image:C4E10AQFoyyAjHPMQuQ"
  }
}
```

Save the `image` URN and the `uploadUrl`.

### Step 2: Upload the Image Binary

```bash
curl -X PUT '{uploadUrl}' \
  -H 'Authorization: Bearer {TOKEN}' \
  -H 'Content-Type: application/octet-stream' \
  --upload-file ./my-image.png
```

**Response:** `201 Created`

### Step 3: Create Post with Image

```bash
curl -X POST 'https://api.linkedin.com/rest/posts' \
  -H 'Authorization: Bearer {TOKEN}' \
  -H 'LinkedIn-Version: 202604' \
  -H 'X-Restli-Protocol-Version: 2.0.0' \
  -H 'Content-Type: application/json' \
  --data '{
    "author": "urn:li:person:{id}",
    "commentary": "Post text with an image attached.",
    "visibility": "PUBLIC",
    "distribution": {
      "feedDistribution": "MAIN_FEED",
      "targetEntities": [],
      "thirdPartyDistributionChannels": []
    },
    "content": {
      "media": {
        "id": "urn:li:image:C4E10AQFoyyAjHPMQuQ",
        "altText": "Description for accessibility"
      }
    },
    "lifecycleState": "PUBLISHED",
    "isReshareDisabledByAuthor": false
  }'
```

**Image specs:**
- Formats: JPG, PNG, GIF (up to 250 frames)
- Max resolution: 36,152,320 pixels

---

## Workflow: Post with Video

Four steps: initialize, upload parts, finalize, create post.

### Step 1: Initialize Video Upload

```bash
curl -X POST 'https://api.linkedin.com/rest/videos?action=initializeUpload' \
  -H 'Authorization: Bearer {TOKEN}' \
  -H 'LinkedIn-Version: 202604' \
  -H 'X-Restli-Protocol-Version: 2.0.0' \
  -H 'Content-Type: application/json' \
  --data '{
    "initializeUploadRequest": {
      "owner": "urn:li:person:{id}",
      "fileSizeBytes": 10485760,
      "uploadCaptions": false,
      "uploadThumbnail": false
    }
  }'
```

**Response** includes `uploadInstructions` (one URL per 4MB chunk), `uploadToken`, and the `video` URN.

### Step 2: Split and Upload Parts

Split the file into 4MB chunks and upload each to its respective URL:

```bash
split -b 4194303 video.mp4 video_part_

curl -X PUT '{uploadUrl_part1}' \
  -H 'Content-Type: application/octet-stream' \
  --upload-file video_part_aa
```

Save the `ETag` from each response header. These are needed for finalization.

### Step 3: Finalize Upload

```bash
curl -X POST 'https://api.linkedin.com/rest/videos?action=finalizeUpload' \
  -H 'Authorization: Bearer {TOKEN}' \
  -H 'LinkedIn-Version: 202604' \
  -H 'X-Restli-Protocol-Version: 2.0.0' \
  -H 'Content-Type: application/json' \
  --data '{
    "finalizeUploadRequest": {
      "video": "urn:li:video:C5505AQH-oV1qvnFtKA",
      "uploadToken": "",
      "uploadedPartIds": [
        "{etag_from_part1}",
        "{etag_from_part2}"
      ]
    }
  }'
```

### Step 4: Create Post with Video

```bash
curl -X POST 'https://api.linkedin.com/rest/posts' \
  -H 'Authorization: Bearer {TOKEN}' \
  -H 'LinkedIn-Version: 202604' \
  -H 'X-Restli-Protocol-Version: 2.0.0' \
  -H 'Content-Type: application/json' \
  --data '{
    "author": "urn:li:person:{id}",
    "commentary": "Post text with video.",
    "visibility": "PUBLIC",
    "distribution": {
      "feedDistribution": "MAIN_FEED",
      "targetEntities": [],
      "thirdPartyDistributionChannels": []
    },
    "content": {
      "media": {
        "title": "Video title",
        "id": "urn:li:video:C5505AQH-oV1qvnFtKA"
      }
    },
    "lifecycleState": "PUBLISHED",
    "isReshareDisabledByAuthor": false
  }'
```

**Video specs:**
- Format: MP4 only
- Duration: 3 seconds to 30 minutes
- File size: 75KB to 500MB
- Optional captions: SRT format, English only
- Optional custom thumbnail: set `uploadThumbnail: true` in init

---

## Workflow: Post with Document

Three steps, same pattern as images. Documents render as swipeable carousels on LinkedIn.

### Step 1: Initialize Document Upload

```bash
curl -X POST 'https://api.linkedin.com/rest/documents?action=initializeUpload' \
  -H 'Authorization: Bearer {TOKEN}' \
  -H 'LinkedIn-Version: 202604' \
  -H 'X-Restli-Protocol-Version: 2.0.0' \
  -H 'Content-Type: application/json' \
  --data '{
    "initializeUploadRequest": {
      "owner": "urn:li:person:{id}"
    }
  }'
```

**Response** includes `uploadUrl` and `document` URN.

### Step 2: Upload the Document Binary

```bash
curl -X PUT '{uploadUrl}' \
  -H 'Authorization: Bearer {TOKEN}' \
  --upload-file ./slides.pdf
```

### Step 3: Create Post with Document

```bash
curl -X POST 'https://api.linkedin.com/rest/posts' \
  -H 'Authorization: Bearer {TOKEN}' \
  -H 'LinkedIn-Version: 202604' \
  -H 'X-Restli-Protocol-Version: 2.0.0' \
  -H 'Content-Type: application/json' \
  --data '{
    "author": "urn:li:person:{id}",
    "commentary": "Swipe through these slides.",
    "visibility": "PUBLIC",
    "distribution": {
      "feedDistribution": "MAIN_FEED",
      "targetEntities": [],
      "thirdPartyDistributionChannels": []
    },
    "content": {
      "media": {
        "title": "Presentation Title",
        "id": "urn:li:document:C5F10AQGKQg_6y2a4sQ"
      }
    },
    "lifecycleState": "PUBLISHED",
    "isReshareDisabledByAuthor": false
  }'
```

**Document specs:**
- Formats: PDF, PPT, PPTX, DOC, DOCX
- Max file size: 100MB
- Max pages: 300

---

## Workflow: Article Post with Link Preview

The API does not support URL scraping. You must manually provide the title, description, and thumbnail.

```bash
curl -X POST 'https://api.linkedin.com/rest/posts' \
  -H 'Authorization: Bearer {TOKEN}' \
  -H 'LinkedIn-Version: 202604' \
  -H 'X-Restli-Protocol-Version: 2.0.0' \
  -H 'Content-Type: application/json' \
  --data '{
    "author": "urn:li:person:{id}",
    "commentary": "Check out this article.",
    "visibility": "PUBLIC",
    "distribution": {
      "feedDistribution": "MAIN_FEED",
      "targetEntities": [],
      "thirdPartyDistributionChannels": []
    },
    "content": {
      "article": {
        "source": "https://example.com/article",
        "thumbnail": "urn:li:image:{id}",
        "title": "Article Title",
        "description": "Short description of the article."
      }
    },
    "lifecycleState": "PUBLISHED",
    "isReshareDisabledByAuthor": false
  }'
```

Upload the thumbnail image first using the Images API workflow above.

---

## Repurposing Media Across Posts

Once uploaded, media assets (images, videos, documents) can be reused in multiple posts without re-uploading. The URN is permanent.

**Example:** Upload an image once, then reference `urn:li:image:C4E10AQFoyyAjHPMQuQ` in any number of future posts.

To verify an asset is still available before reusing it:

```bash
# Check image status
curl -s 'https://api.linkedin.com/rest/images/urn:li:image:{id}' \
  -H 'Authorization: Bearer {TOKEN}' \
  -H 'LinkedIn-Version: 202604' | jq '.status'

# Check video status
curl -s 'https://api.linkedin.com/rest/videos/urn%3Ali%3Avideo%3A{id}' \
  -H 'Authorization: Bearer {TOKEN}' \
  -H 'LinkedIn-Version: 202604' | jq '.status'

# Check document status
curl -s 'https://api.linkedin.com/rest/documents/urn:li:document:{id}' \
  -H 'Authorization: Bearer {TOKEN}' \
  -H 'LinkedIn-Version: 202604' | jq '.status'
```

Status should be `AVAILABLE`. Other statuses: `PROCESSING`, `PROCESSING_FAILED`, `WAITING_UPLOAD`.

**Batch check** multiple assets in one call:

```bash
curl -s 'https://api.linkedin.com/rest/images?ids=List(urn%3Ali%3Aimage%3A{id1},urn%3Ali%3Aimage%3A{id2})' \
  -H 'Authorization: Bearer {TOKEN}' \
  -H 'LinkedIn-Version: 202604' \
  -H 'X-RestLi-Method: BATCH_GET'
```

---

## Managing Published Posts

### Edit Post Text

```bash
curl -X POST 'https://api.linkedin.com/rest/posts/{encoded_post_urn}' \
  -H 'Authorization: Bearer {TOKEN}' \
  -H 'LinkedIn-Version: 202604' \
  -H 'X-Restli-Protocol-Version: 2.0.0' \
  -H 'X-RestLi-Method: PARTIAL_UPDATE' \
  -H 'Content-Type: application/json' \
  --data '{
    "patch": {
      "$set": {
        "commentary": "Updated post text."
      }
    }
  }'
```

Updatable fields: `commentary`, `contentCallToActionLabel`, `contentLandingPage`, `lifecycleState`.

### Delete a Post

```bash
curl -X DELETE 'https://api.linkedin.com/rest/posts/{encoded_post_urn}' \
  -H 'Authorization: Bearer {TOKEN}' \
  -H 'LinkedIn-Version: 202604' \
  -H 'X-Restli-Protocol-Version: 2.0.0' \
  -H 'X-RestLi-Method: DELETE'
```

Returns `204`. Idempotent (deleting an already-deleted post also returns `204`).

### Get Engagement Stats

```bash
curl -s 'https://api.linkedin.com/rest/socialMetadata/{post_urn}' \
  -H 'Authorization: Bearer {TOKEN}' \
  -H 'LinkedIn-Version: 202604' \
  -H 'X-Restli-Protocol-Version: 2.0.0'
```

Returns reaction counts by type (LIKE, PRAISE, EMPATHY, INTEREST, APPRECIATION, MAYBE) and comment counts.

### Enable or Disable Comments

```bash
curl -X POST 'https://api.linkedin.com/rest/socialMetadata/{post_urn}?actor={person_urn}' \
  -H 'Authorization: Bearer {TOKEN}' \
  -H 'LinkedIn-Version: 202604' \
  -H 'X-Restli-Protocol-Version: 2.0.0' \
  -H 'X-RestLi-Method: PARTIAL_UPDATE' \
  -H 'Content-Type: application/json' \
  --data '{
    "patch": {
      "$set": {
        "commentsState": "CLOSED"
      }
    }
  }'
```

Set to `OPEN` to re-enable. Disabling comments deletes all existing comments on the post.

---

## Visibility Options

| Value | Who sees it |
|---|---|
| `PUBLIC` | Anyone on or off LinkedIn |
| `CONNECTIONS` | Your 1st-degree connections only |
| `LOGGED_IN` | Any logged-in LinkedIn member |
| `CONTAINER` | Delegated to the container (e.g., a group) |

There is no `PRIVATE` or `SELF` visibility. `CONNECTIONS` is the most restrictive option available.

---

## Mentions and Hashtags

**Mention an organization:**

```
"commentary": "Great work by @[Company Name](urn:li:organization:123456)"
```

The text inside `@[...]` must match the organization name exactly (case-sensitive).

**Mention a person:**

```
"commentary": "Congrats @[Jane Smith](urn:li:person:abc123)"
```

Person mentions only need to match one name (first or last).

**Hashtags:**

```
"commentary": "Thoughts on this approach #MachineLearning #Python"
```

---

## API Constraints and Limitations

| Constraint | Detail |
|---|---|
| Draft creation | Not supported. `lifecycleState` must be `PUBLISHED` at creation time |
| Post scheduling | Not available in the API. Use external cron (this repo uses GitHub Actions) |
| URL scraping | Not supported for article posts. Must manually set title, description, thumbnail |
| Organic carousels | Not supported. Carousels are sponsored-only |
| Commentary length | 3,000 characters max |
| Targeted organic posts | Organization-authored only, audience must exceed 300 members |
| Rate limiting | 429 status code when exceeded. Implement backoff |
| Token expiry | 60 days. This repo checks weekly via `.github/workflows/token-expiry-check.yml` |
| Version sunset | Versions are supported for 1 year minimum. Currently on 202604 |
| Read own posts | Requires `r_member_social` permission (restricted, requires approval) |

---

---

## Reference

Official LinkedIn API documentation (all links are for version 202604):

| Resource | URL |
|---|---|
| Posts API | https://learn.microsoft.com/en-us/linkedin/marketing/community-management/shares/posts-api?view=li-lms-2026-04 |
| Post API Schema | https://learn.microsoft.com/en-us/linkedin/marketing/community-management/shares/post-api-schema?view=li-lms-2026-04 |
| Images API | https://learn.microsoft.com/en-us/linkedin/marketing/community-management/shares/images-api?view=li-lms-2026-04 |
| Videos API | https://learn.microsoft.com/en-us/linkedin/marketing/community-management/shares/videos-api?view=li-lms-2026-04 |
| Documents API | https://learn.microsoft.com/en-us/linkedin/marketing/community-management/shares/documents-api?view=li-lms-2026-04 |
| Social Metadata API | https://learn.microsoft.com/en-us/linkedin/marketing/community-management/shares/social-metadata-api?view=li-lms-2026-04 |
| Comments API | https://learn.microsoft.com/en-us/linkedin/marketing/community-management/shares/comments-api?view=li-lms-2026-04 |
| API Versioning | https://learn.microsoft.com/en-us/linkedin/marketing/versioning?view=li-lms-2026-04 |
| Content Migration Guide | https://learn.microsoft.com/en-us/linkedin/marketing/community-management/contentapi-migration-guide?view=li-lms-2026-04 |
| OAuth Token Generator | https://www.linkedin.com/developers/tools/oauth/token-generator |
| LinkedIn Developer Portal | https://www.linkedin.com/developers |
| Developer Support | https://linkedin.zendesk.com/hc/en-us |
