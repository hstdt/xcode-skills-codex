# Xcode Skills for Codex

Apple-authored skills exported from Xcode in its native Codex plugin format, automatically maintained by GitHub Actions and `github-actions[bot]`.

<!-- snapshot:start -->
Xcode **27.0 (27A266a)** · Exported 2026-09-18 · 15 skills
<!-- snapshot:end -->

## Skills

<!-- skills:start -->
| Area | Skills |
| --- | --- |
| Accessibility | [accessibility-dynamic-type-specialist](skills/accessibility-dynamic-type-specialist/SKILL.md), [accessibility-sufficient-contrast-specialist](skills/accessibility-sufficient-contrast-specialist/SKILL.md), [accessibility-voiceover-specialist](skills/accessibility-voiceover-specialist/SKILL.md) |
| Modernization and safety | [adopt-c-bounds-safety](skills/adopt-c-bounds-safety/SKILL.md), [audit-xcode-security-settings](skills/audit-xcode-security-settings/SKILL.md), [modernize-tests](skills/modernize-tests/SKILL.md), [uikit-app-modernization](skills/uikit-app-modernization/SKILL.md) |
| App Intents | [app-intents-specialist](skills/app-intents-specialist/SKILL.md), [app-intents-whats-new-27](skills/app-intents-whats-new-27/SKILL.md) |
| SwiftUI | [building-document-based-swiftui-applications](skills/building-document-based-swiftui-applications/SKILL.md), [swiftui-specialist](skills/swiftui-specialist/SKILL.md), [swiftui-whats-new-27](skills/swiftui-whats-new-27/SKILL.md) |
| Device verification | [device-interaction](skills/device-interaction/SKILL.md) |
| Localization | [translation](skills/translation/SKILL.md), [translation-coordinator](skills/translation-coordinator/SKILL.md) |
<!-- skills:end -->

## Automated updates

The [Update Xcode skills](https://github.com/hstdt/xcode-skills-codex/actions/workflows/update.yml) workflow runs daily or manually via **Run workflow**. GitHub's `xcode-27` runner selects its newest installed Xcode, including betas, and uses the headless Xcode Service to export the native Codex plugin:

```sh
xcrun agent plugin path --plugin-format codex
```

On the first run or when a newer Xcode version or build is available, the workflow replaces `skills/` and `.codex-plugin/`, refreshes the snapshot metadata and skill list, and pushes the update to `main` as `github-actions[bot]`. Exported content is preserved as supplied by Apple. Updates follow Xcode availability on GitHub's runner images.

## Attribution

Skill content is authored by Apple and supplied with Xcode. This repository is independently maintained; Apple's applicable terms govern the exported content.
