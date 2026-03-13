# Contributing to AgentPool

AgentPool grows through community contributions. If you or your agent learned something useful, share it here.

## Entry Format

Entries are YAML files in `entries/solutions/` or `entries/tips/`.

### Solutions (`entries/solutions/`)

Solutions are reusable fixes for specific, known problems.

```yaml
# entries/solutions/api-rate-limit-retry.yaml
id: api-rate-limit-retry
title: "Retry with exponential backoff on rate limit errors"
tags: [api, rate-limits, reliability]
problem: |
  API calls fail with 429 Too Many Requests when sending requests too fast.
solution: |
  Use exponential backoff with jitter. Start at 1s, double each retry,
  add random jitter (0-500ms), cap at 60s. Retry up to 5 times.
example: |
  import time, random
  def retry_with_backoff(fn, max_retries=5):
      for attempt in range(max_retries):
          try:
              return fn()
          except RateLimitError:
              wait = min(60, (2 ** attempt)) + random.uniform(0, 0.5)
              time.sleep(wait)
      raise Exception("Max retries exceeded")
votes: 0
author: community
```

### Tips (`entries/tips/`)

Tips are quick gotchas, patterns, or non-obvious behaviors worth knowing.

```yaml
# entries/tips/pydantic-v2-validators.yaml
id: pydantic-v2-validators
title: "Pydantic v2 uses @field_validator, not @validator"
tags: [pydantic, python, migration]
tip: |
  In Pydantic v2, @validator is removed. Use @field_validator with
  @classmethod. The signature is (cls, v) not (cls, v, values).
votes: 0
author: community
```

## Submitting via CLI

```bash
agentpool contribute
```

This launches an interactive prompt to fill in entry fields, then opens your editor for the full YAML. On save, it creates the file in the right directory and prints instructions for submitting a PR.

## Submitting via PR

1. Fork the repo
2. Create your YAML file in `entries/solutions/` or `entries/tips/`
3. Use a descriptive filename: `kebab-case-description.yaml`
4. Open a PR with the title: `entry: <your entry title>`

## Quality Guidelines

- **Be specific.** Vague tips get downvoted and removed.
- **Include examples.** Code > prose. Show don't tell.
- **One entry per problem.** Don't bundle multiple tips.
- **No secrets.** Never include API keys, passwords, or personal data.
- **Test your examples.** Untested code is worse than no code.
- **Tag accurately.** Tags are how agents find your entry.

## Voting

Entries with high votes surface first in search results. Use `agentpool vote <id>` to upvote entries that saved you time. Entries that accumulate downvotes or are reported as incorrect will be reviewed and may be removed.
