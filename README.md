# Xcode Skills for Codex

Apple-authored skills exported from Xcode in its native Codex plugin format, automatically maintained by GitHub Actions and `github-actions[bot]`.

<!-- snapshot:start -->
Awaiting the first automated export.
<!-- snapshot:end -->

## Skills

<!-- skills:start -->
<!-- skills:end -->

## Automated updates

The [Update Xcode skills](https://github.com/hstdt/xcode-skills-codex/actions/workflows/update.yml) workflow runs daily or manually via **Run workflow**. GitHub's `xcode-27` runner selects its newest installed Xcode, including betas, and uses the headless Xcode Service to export the native Codex plugin:

```sh
xcrun agent plugin path --plugin-format codex
```

On the first run or when a newer Xcode version or build is available, the workflow replaces `skills/` and `.codex-plugin/`, refreshes the snapshot metadata and skill list, and pushes the update to `main` as `github-actions[bot]`. Exported content is preserved as supplied by Apple. Updates follow Xcode availability on GitHub's runner images.

## Attribution

Skill content is authored by Apple and supplied with Xcode. This repository is independently maintained; Apple's applicable terms govern the exported content.
