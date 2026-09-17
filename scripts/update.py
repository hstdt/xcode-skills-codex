"""Export a newer installed Xcode without modifying Apple's exported files."""
import argparse
import datetime
import json
import os
import plistlib
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import time

from diagnostics import collect_safely

ROOT = Path(__file__).resolve().parents[1]


def version_key(version, build):
    parts = tuple(int(p) for p in version.split("."))
    if len(parts) > 3:
        raise ValueError(f"Unsupported Xcode version: {version}")
    match = re.fullmatch(r"(\d+)([A-Z])(\d+)([a-z]?)", build)
    if not match:
        raise ValueError(f"Unsupported Xcode build: {build}")
    major, train, number, suffix = match.groups()
    number = int(number)
    # Apple development builds use the 5000+ range. Release builds must
    # sort after them, even though their numeric build component is smaller.
    release = number < 5000
    return (parts + (0,) * (3 - len(parts)), int(major), train,
            release, number, -ord(suffix) if suffix else 0)


def installed_xcodes():
    seen = set()
    for app in Path("/Applications").glob("Xcode*.app"):
        developer = (app / "Contents/Developer").resolve()
        if developer in seen or not developer.is_dir():
            continue
        seen.add(developer)
        env = dict(os.environ, DEVELOPER_DIR=str(developer))
        output = subprocess.check_output(["xcodebuild", "-version"], env=env, text=True)
        version = re.search(r"^Xcode ([\d.]+)$", output, re.M)
        build = re.search(r"^Build version (\S+)$", output, re.M)
        if not version or not build:
            raise ValueError(f"Cannot read Xcode version: {output}")
        yield version.group(1), build.group(1), env


def render_readme(text, snapshot, names):
    summary = (f"Xcode **{snapshot['xcode_version']} ({snapshot['xcode_build']})** · "
               f"Exported {snapshot['export_date']} · {len(names)} skills")
    text, count = re.subn(r"(?<=<!-- snapshot:start -->).*?(?=<!-- snapshot:end -->)",
                          "\n" + summary + "\n", text, flags=re.S)
    if count != 1:
        raise ValueError("README snapshot markers are missing or duplicated")
    groups = {}
    for name in names:
        if name.startswith("swiftui-") or "document-based" in name:
            group = "SwiftUI"
        elif name.startswith("app-intents-"):
            group = "App Intents"
        elif name.startswith("accessibility-"):
            group = "Accessibility"
        elif name.startswith("translation"):
            group = "Localization"
        elif name == "device-interaction":
            group = "Device verification"
        elif name in {"uikit-app-modernization", "modernize-tests", "adopt-c-bounds-safety", "audit-xcode-security-settings"}:
            group = "Modernization and safety"
        else:
            group = "Other"
        groups.setdefault(group, []).append(name)
    table = ["| Area | Skills |", "| --- | --- |"]
    for group, members in groups.items():
        links = ", ".join(f"[{name}](skills/{name}/SKILL.md)" for name in members)
        table.append(f"| {group} | {links} |")
    text, count = re.subn(r"(?<=<!-- skills:start -->).*?(?=<!-- skills:end -->)",
                          "\n" + "\n".join(table) + "\n", text, flags=re.S)
    if count != 1:
        raise ValueError("README skills markers are missing or duplicated")
    return text


def prepare_xcode(env):
    if env.get("GITHUB_ACTIONS") != "true" or env.get("RUNNER_ENVIRONMENT") != "github-hosted":
        raise RuntimeError("--prepare-xcode requires a disposable GitHub-hosted runner")
    developer = Path(env["DEVELOPER_DIR"])
    subprocess.run(["sudo", "env", f"DEVELOPER_DIR={developer}",
                    "xcodebuild", "-runFirstLaunch"], check=True, timeout=300)
    subprocess.run(["sudo", "env", f"DEVELOPER_DIR={developer}",
                    "xcrun", "mcp-server", "enable", "--unsafe-always-allow-all-agents"],
                   check=True, timeout=60)
    try:
        # Launch only the headless service; opening a workspace can present
        # a modal alert that prevents the service from answering requests.
        service = developer / "Library/Xcode/Agents/Xcode Service.app"
        info = plistlib.loads((service / "Contents/Info.plist").read_bytes())
        if info.get("CFBundleIdentifier") != "com.apple.dt.mcp-server":
            raise RuntimeError(f"Unexpected headless service bundle: {service}")
        subprocess.run(["open", "-g", "-a", str(service)],
                       check=True, env=env, timeout=30)
        return export_plugin(env, attempts=12)
    except Exception as error:
        collect_safely(env, str(error))
        raise
    finally:
        subprocess.run(["sudo", "env", f"DEVELOPER_DIR={developer}",
                        "xcrun", "mcp-server", "disable"], check=True, timeout=30)


def export_plugin(env, attempts=1):
    timeouts = 0
    for attempt in range(attempts):
        try:
            output = subprocess.check_output(
                ["xcrun", "agent", "plugin", "path", "--plugin-format", "codex"],
                env=env, text=True, timeout=60)
        except subprocess.TimeoutExpired:
            timeouts += 1
            collect_safely(env, "Plugin export timed out after 60 seconds")
            print("Plugin export timed out; inspecting headless service", flush=True)
            subprocess.run(["xcrun", "mcp-server", "status", "--format", "json"],
                           env=env, timeout=30)
            if timeouts >= 2 or attempt + 1 == attempts:
                raise RuntimeError("Plugin export timed out; snapshot left unchanged") from None
            time.sleep(5)
            continue
        source = Path(output.strip())
        if not source.is_absolute() or not source.is_dir():
            raise ValueError(f"Invalid export path: {output!r}")
        if any((source / "skills").glob("*/SKILL.md")):
            return source
        if attempt + 1 < attempts:
            print(f"Waiting for Xcode skills ({attempt + 1}/{attempts})", flush=True)
            time.sleep(5)
    subprocess.run(["xcrun", "mcp-server", "status"], env=env, timeout=30)
    raise RuntimeError("Xcode service did not provide any skills; snapshot left unchanged")


def main(prepare=False):
    snapshot_path = ROOT / "snapshot.json"
    current = json.loads(snapshot_path.read_text()) if snapshot_path.exists() else None
    candidates = list(installed_xcodes())
    if not candidates:
        raise RuntimeError("No Xcode installation found")
    version, build, env = max(candidates, key=lambda c: version_key(c[0], c[1]))
    if current is not None and version_key(version, build) <= version_key(current["xcode_version"], current["xcode_build"]):
        print(f"No newer Xcode: runner {version} ({build}); snapshot {current['xcode_version']} ({current['xcode_build']})")
        return
    source = prepare_xcode(env) if prepare else export_plugin(env)
    with tempfile.TemporaryDirectory() as directory:
        staged = Path(directory)
        for name in ("skills", ".codex-plugin"):
            shutil.copytree(source / name, staged / name)
        manifest = json.loads((staged / ".codex-plugin/plugin.json").read_text())
        if manifest.get("skills") not in ("./skills/", "./skills", "skills/", "skills"):
            raise ValueError("Unexpected plugin skills path")
        folders = sorted(p for p in (staged / "skills").iterdir() if p.is_dir())
        if not folders:
            raise ValueError("Export contains no skills")
        for folder in folders:
            content = (folder / "SKILL.md").read_text()
            if not content.startswith("---\n") or not re.search(r"^name:", content, re.M) or not re.search(r"^description:", content, re.M):
                raise ValueError(f"Invalid skill: {folder.name}")
        snapshot = dict(xcode_version=version, xcode_build=build,
                        export_date=datetime.datetime.now(datetime.timezone.utc).date().isoformat(),
                        skill_count=len(folders))
        readme = render_readme((ROOT / "README.md").read_text(), snapshot, [p.name for p in folders])
        # Complete export and validation before touching the existing snapshot.
        for name in ("skills", ".codex-plugin"):
            if (ROOT / name).exists():
                shutil.rmtree(ROOT / name)
            shutil.copytree(staged / name, ROOT / name)
        (ROOT / "snapshot.json").write_text(json.dumps(snapshot, indent=2) + "\n")
        (ROOT / "README.md").write_text(readme)
        print(f"Exported Xcode {version} ({build}): {len(folders)} skills")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--prepare-xcode", action="store_true",
                        help="Initialize and launch Xcode service on the CI runner")
    main(prepare=parser.parse_args().prepare_xcode)
