#!/usr/bin/env python3
"""Post the next queued LinkedIn post via the LinkedIn API."""

import json
import os
import random
import shutil
import sys
import urllib.error
import urllib.request

QUEUE_PATH = "linkedin/.post-queue"
NOT_POSTED_DIR = "linkedin/not-posted"
POSTED_DIR = "linkedin/posted"


def read_queue():
    if not os.path.exists(QUEUE_PATH):
        return []
    with open(QUEUE_PATH, "r") as f:
        return [line.strip() for line in f if line.strip()]


def write_queue(slugs):
    with open(QUEUE_PATH, "w") as f:
        for slug in slugs:
            f.write(slug + "\n")


def get_post_files(directory):
    if not os.path.exists(directory):
        return []
    return [f for f in os.listdir(directory) if f.endswith(".md")]


def recycle_posts():
    """Move all posts from posted/ back to not-posted/ in randomized order."""
    posted_files = get_post_files(POSTED_DIR)
    if not posted_files:
        print("Both not-posted/ and posted/ are empty. Nothing to recycle.")
        return []

    print(f"Recycling {len(posted_files)} posts from posted/ back to not-posted/")
    os.makedirs(NOT_POSTED_DIR, exist_ok=True)

    for filename in posted_files:
        src = os.path.join(POSTED_DIR, filename)
        dst = os.path.join(NOT_POSTED_DIR, filename)
        shutil.move(src, dst)

    slugs = [f.replace(".md", "") for f in posted_files]
    random.shuffle(slugs)
    write_queue(slugs)
    print(f"New randomized queue: {len(slugs)} posts")
    return slugs


def post_to_linkedin(text, access_token, person_urn, visibility="PUBLIC"):
    url = "https://api.linkedin.com/rest/posts"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
        "X-Restli-Protocol-Version": "2.0.0",
        "LinkedIn-Version": "202604",
    }
    payload = {
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
    dry_run = os.environ.get("DRY_RUN", "false").lower() == "true"
    access_token = os.environ.get("LINKEDIN_ACCESS_TOKEN", "")
    person_urn = os.environ.get("LINKEDIN_PERSON_URN", "")

    if not access_token or not person_urn:
        print("ERROR: LINKEDIN_ACCESS_TOKEN and LINKEDIN_PERSON_URN must be set")
        sys.exit(1)

    queue = read_queue()

    if not queue or not get_post_files(NOT_POSTED_DIR):
        queue = recycle_posts()
        if not queue:
            sys.exit(0)

    slug = queue[0]
    print(f"Next in queue: {slug}")

    filepath = os.path.join(NOT_POSTED_DIR, f"{slug}.md")
    if not os.path.exists(filepath):
        print(f"WARNING: {filepath} not found. Removing from queue.")
        write_queue(queue[1:])
        sys.exit(0)

    with open(filepath, "r") as f:
        body = f.read().strip()
    print(f"Post length: {len(body)} characters")

    if len(body) > 3000:
        print(f"WARNING: Truncating from {len(body)} to 3000 characters")
        body = body[:3000]

    if dry_run:
        print("=== DRY RUN (posting to CONNECTIONS only) ===")
        success = post_to_linkedin(body, access_token, person_urn, visibility="CONNECTIONS")
        if not success:
            sys.exit(1)
        print("Dry run complete. Queue and files unchanged.")
        return

    success = post_to_linkedin(body, access_token, person_urn)
    if not success:
        sys.exit(1)

    os.makedirs(POSTED_DIR, exist_ok=True)
    dst = os.path.join(POSTED_DIR, f"{slug}.md")
    shutil.move(filepath, dst)
    print(f"Moved {filepath} -> {dst}")

    write_queue(queue[1:])
    with open("linkedin/.post-queue.last", "w") as f:
        f.write(slug)
    print(f"Done. {len(queue) - 1} posts remaining in queue.")


if __name__ == "__main__":
    main()
