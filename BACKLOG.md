# Backlog

## ci-test-gate: PR #88 gate stays red until the contributor's branch is rebased

**Status:** needs a maintainer decision — not actioned
**Date:** 2026-10-01

The `CI Test Gate` workflow on `main` is fixed, but `pull_request` runs execute the
workflow file **from the head branch**, and fork PR #88 (`ahcrm-core`) still carries
the old `test-gate.yml` with `github-script@v7` and the vulnerable `${{ }}`
interpolation. Reruns keep failing at "Comment on PR", so that check stays red until
the branch picks up the fixed file.

**Why this was not just done:** pushing to a contributor's fork is a decision about
someone else's branch. Options:

1. Ask `ahcrm-core` to rebase onto `main` (cleanest, the branch stays theirs).
2. Push the workflow change to their fork directly (fastest, but writes to a third party's repo).
3. Leave the check red and treat it as informational until the contributor updates.

**Open question:** which option is the house policy for stale workflow files on
incoming forks.

## ci-test-gate: `sarif.py` has 0% test coverage

**Status:** candidate for a follow-up contribution
**Date:** 2026-10-01

`src/ci_test_gate/sarif.py` (16 statements) is never imported by any test, so the
`--output sarif` path of the CLI is entirely unexercised. Overall coverage is 89%.
Worth a dedicated test module; noted while validating the CI fix.