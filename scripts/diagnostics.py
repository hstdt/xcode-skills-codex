"""Print bounded Xcode/MCP diagnostics before the headless service is stopped."""
import subprocess

_COLLECTED = False


def capture(command, env, timeout=20):
    try:
        result = subprocess.run(command, env=env, stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT, text=True, timeout=timeout)
        return result.stdout + f"\n[exit code: {result.returncode}]"
    except subprocess.TimeoutExpired as error:
        partial = error.stdout or ""
        if isinstance(partial, bytes):
            partial = partial.decode(errors="replace")
        return partial + f"\n[timed out after {timeout}s]"
    except OSError as error:
        return f"[diagnostic command failed: {error}]"


def section(title, content, limit=16000):
    print(f"\n=== XCODE DIAGNOSTIC: {title} ===", flush=True)
    print(content[:limit], flush=True)
    if len(content) > limit:
        print(f"[truncated at {limit} characters]", flush=True)


def collect(env, reason):
    global _COLLECTED
    if _COLLECTED:
        return
    _COLLECTED = True
    section("reason", reason)
    section("Xcode version", capture(["xcodebuild", "-version"], env))
    section("macOS version", capture(["sw_vers"], env))
    # Only executable names/paths; never dump process arguments or environment.
    output = capture(["ps", "-axo", "pid=,ppid=,stat=,etime=,comm="], env)
    relevant = []
    candidates = []
    for line in output.splitlines():
        fields = line.split(None, 4)
        if len(fields) != 5 or not fields[0].isdigit():
            continue
        executable = fields[4].lower()
        if any(name in executable for name in ("xcodeservice", "mcp", "/xcode")):
            relevant.append(line)
            candidates.append((0 if "xcodeservice" in executable else 1, fields[0]))
    section("Xcode/MCP processes", "\n".join(relevant) or "No matching processes")
    for _, pid in sorted(candidates)[:2]:
        section(f"process sample PID {pid}", capture(
            ["sudo", "-n", "/usr/bin/sample", pid, "3", "10"], env, timeout=15), limit=24000)
    section("MCP status", capture(
        ["xcrun", "mcp-server", "status", "--format", "json"], env, timeout=35))
    section("recent Xcode/MCP logs", capture(
        ["/usr/bin/log", "show", "--last", "5m", "--style", "compact", "--info",
         "--predicate", 'process CONTAINS[c] "Xcode" OR process CONTAINS[c] "mcp"'],
        env, timeout=30)[-24000:], limit=24000)


def collect_safely(env, reason):
    try:
        collect(env, reason)
    except Exception as error:
        print(f"Xcode diagnostics failed: {error}", flush=True)
