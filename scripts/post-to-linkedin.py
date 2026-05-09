#!/usr/bin/env python3
"""Post the next LinkedIn post via the LinkedIn API."""

import argparse
import json
import os
import random
import shutil
import sys
import urllib.error
import urllib.request

NOT_POSTED_DIR = "linkedin/not-posted"
POSTED_DIR = "linkedin/posted"


def get_post_files(directory):
    if not os.path.exists(directory):
        return []
    return [f for f in os.listdir(directory) if f.endswith(".md")]


def recycle_posts():
    """Move all posts from posted/ back to not-posted/."""
    posted_files = get_post_files(POSTED_DIR)
    if not posted_files:
        return False

    print(f"Recycling {len(posted_files)} posts from posted/ back to not-posted/")
    os.makedirs(NOT_POSTED_DIR, exist_ok=True)

    for filename in posted_files:
        src = os.path.join(POSTED_DIR, filename)
        dst = os.path.join(NOT_POSTED_DIR, filename)
        shutil.move(src, dst)

    return True


def build_payload(text, person_urn, visibility="PUBLIC"):
    return {
        "author": person_urn,
        "commentary": text,
        "visibility": visibility,
        "distribution": {
            "feedDistribution": "MAIN_FEED",
            "targetEntities": [],
            "thirdPartyDistributionChannels": [],
        },
        "lifecycleState": "PUBLISHED",
        "isReshareDisabledByAuthor": False,
    }


def post_to_linkedin(payload, access_token):
    url = "https://api.linkedin.com/rest/posts"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
        "X-Restli-Protocol-Version": "2.0.0",
        "LinkedIn-Version": "202604",
    }

    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    try:
        response = urllib.request.urlopen(req)
        status = response.getcode()
        print(f"Posted successfully. Status: {status}")
        post_id = response.headers.get("x-restli-id", "")
        if post_id:
            print(f"Post ID: {post_id}")
        return True
    except urllib.error.HTTPError as e:
        print(f"ERROR: LinkedIn API returned {e.code}")
        print(f"Response: {e.read().decode()}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Post to LinkedIn")
    parser.add_argument("--preview", action="store_true",
                        help="Print API payload without making any API call")
    args = parser.parse_args()

    dry_run = os.environ.get("DRY_RUN", "false").lower() == "true"
    access_token = os.environ.get("LINKEDIN_ACCESS_TOKEN", "")
    person_urn = os.environ.get("LINKEDIN_PERSON_URN", "")

    if not args.preview and (not access_token or not person_urn):
        print("ERROR: LINKEDIN_ACCESS_TOKEN and LINKEDIN_PERSON_URN must be set")
        sys.exit(1)

    files = get_post_files(NOT_POSTED_DIR)
    if not files:
        if not recycle_posts():
            print("ERROR: No posts in not-posted/ or posted/. Nothing to publish.")
            sys.exit(1)
        files = get_post_files(NOT_POSTED_DIR)

    filename = random.choice(files)
    slug = filename.replace(".md", "")
    filepath = os.path.join(NOT_POSTED_DIR, filename)
    print(f"Selected: {slug}")

    with open(filepath, "r") as f:
        body = f.read().strip()
    print(f"Post length: {len(body)} characters")

    if len(body) > 3000:
        print(f"WARNING: Truncating from {len(body)} to 3000 characters")
        body = body[:3000]

    if dry_run:
        visibility = "CONNECTIONS"
    else:
        visibility = "PUBLIC"

    payload = build_payload(body, person_urn or "preview-mode", visibility)
    print("=== API PAYLOAD ===")
    print(json.dumps(payload, indent=2))
    print("===================")

    if args.preview:
        print("Preview complete. No API call made.")
        return

    if dry_run:
        print("=== DRY RUN (posting to CONNECTIONS only) ===")

    success = post_to_linkedin(payload, access_token)
    if not success:
        sys.exit(1)

    if dry_run:
        print("Dry run complete. Files unchanged.")
        return

    os.makedirs(POSTED_DIR, exist_ok=True)
    dst = os.path.join(POSTED_DIR, filename)
    shutil.move(filepath, dst)
    print(f"Moved {filepath} -> {dst}")

    with open("linkedin/.post-queue.last", "w") as f:
        f.write(slug)

    remaining = len(get_post_files(NOT_POSTED_DIR))
    print(f"Done. {remaining} posts remaining in not-posted/.")


if __name__ == "__main__":
    main()
