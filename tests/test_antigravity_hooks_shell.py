"""End-to-end shell tests for the Antigravity hook scripts.

Invokes the bash scripts directly via subprocess with synthetic stdin
JSON and asserts on their stdout / exit code / state-dir side effects.

The two scripts under test are:

* `hooks/antigravity/mempal_save_hook_antigravity.sh`  — Stop event
* `hooks/antigravity/mempal_wake_hook_antigravity.sh`  — PreInvocation event

Test isolation:

* Each test runs in its own temp dir.
* `MEMPAL_STATE_DIR` is overridden to point at the temp dir, so no
  test ever touches the real `~/.mempalace/hook_state/`.
* `HOME` is overridden to a temp dir as well so the kill-switch
  palace-existence check sees a hermetic state.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
HOOKS_DIR = REPO_ROOT / "hooks" / "antigravity"
SAVE_HOOK = HOOKS_DIR / "mempal_save_hook_antigravity.sh"
WAKE_HOOK = HOOKS_DIR / "mempal_wake_hook_antigravity.sh"
COMMON_LIB = HOOKS_DIR / "lib" / "common.sh"

# Skip the entire module on Windows — bash 3.2+ is required.
pytestmark = pytest.mark.skipif(
    os.name == "nt",
    reason="Antigravity shell hooks require bash; Windows uses a separate code path.",
)


def _run_hook(
    script: Path,
    stdin_json: dict | str,
    state_dir: Path,
    home: Path,
    extra_env: dict[str, str] | None = None,
    timeout: float = 10.0,
) -> subprocess.CompletedProcess:
    """Run a hook script with isolated env and synthetic stdin."""
    if isinstance(stdin_json, dict):
        stdin = json.dumps(stdin_json)
    else:
        stdin = stdin_json
    env = os.environ.copy()
    # Hermetic env: HOME and state dir point at the test temp.
    home.mkdir(parents=True, exist_ok=True)
    state_dir.mkdir(parents=True, exist_ok=True)
    env["HOME"] = str(home)
    env["MEMPAL_STATE_DIR"] = str(state_dir)
    # Drop any leftover kill-switch envs from the user's environment so
    # the test exercises the gate it intends to.
    for k in ("MEMPAL_DISABLE_HOOK", "MEMPALACE_HOOKS_AUTO_SAVE", "MEMPAL_SAVE_INTERVAL"):
        env.pop(k, None)
    if extra_env:
        env.update(extra_env)
    return subprocess.run(
        ["bash", str(script)],
        input=stdin,
        capture_output=True,
        text=True,
        env=env,
        timeout=timeout,
    )


def _ensure_palace(home: Path) -> None:
    """Create $HOME/.mempalace/ so the palace-nuke kill switch passes."""
    (home / ".mempalace").mkdir(parents=True, exist_ok=True)


def _stop_payload(**overrides) -> dict:
    base = {
        "executionNum": 1,
        "terminationReason": "model_stop",
        "error": "",
        "fullyIdle": True,
        "conversationId": "test-conv-001",
        "workspacePaths": ["/tmp/test-workspace"],
        "transcriptPath": "/tmp/test-transcript.jsonl",
        "artifactDirectoryPath": "/tmp/test-artifacts/",
    }
    base.update(overrides)
    return base


def _wake_payload(**overrides) -> dict:
    base = {
        "invocationNum": 1,
        "initialNumSteps": 0,
        "conversationId": "test-conv-001",
        "workspacePaths": ["/tmp/test-workspace"],
        "transcriptPath": "/tmp/test-transcript.jsonl",
        "artifactDirectoryPath": "/tmp/test-artifacts/",
    }
    base.update(overrides)
    return base


# ── Syntax (bash -n) ──────────────────────────────────────────────────


@pytest.mark.parametrize("script", [SAVE_HOOK, WAKE_HOOK, COMMON_LIB], ids=lambda p: p.name)
def test_bash_n_clean(script: Path) -> None:
    """All shell files parse cleanly under bash 3.2+."""
    result = subprocess.run(
        ["bash", "-n", str(script)],
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert result.returncode == 0, f"bash -n {script.name} failed:\n{result.stderr}"


# ── Save hook ─────────────────────────────────────────────────────────


def test_save_hook_emits_empty_object_on_kill_switch_env(tmp_path: Path) -> None:
    """MEMPAL_DISABLE_HOOK=1 should silently emit `{}` and exit 0."""
    state = tmp_path / "state"
    home = tmp_path / "home"
    _ensure_palace(home)
    result = _run_hook(
        SAVE_HOOK,
        _stop_payload(),
        state_dir=state,
        home=home,
        extra_env={"MEMPAL_DISABLE_HOOK": "1"},
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "{}", result.stdout


def test_save_hook_emits_empty_object_on_auto_save_false(tmp_path: Path) -> None:
    """MEMPALACE_HOOKS_AUTO_SAVE=false short-circuits."""
    state = tmp_path / "state"
    home = tmp_path / "home"
    _ensure_palace(home)
    result = _run_hook(
        SAVE_HOOK,
        _stop_payload(),
        state_dir=state,
        home=home,
        extra_env={"MEMPALACE_HOOKS_AUTO_SAVE": "false"},
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "{}"


def test_save_hook_emits_empty_object_when_palace_dir_missing(tmp_path: Path) -> None:
    """Removing $HOME/.mempalace acts as the strongest kill switch."""
    state = tmp_path / "state"
    home = tmp_path / "home"
    home.mkdir()
    # Deliberately do NOT create ~/.mempalace
    result = _run_hook(SAVE_HOOK, _stop_payload(), state_dir=state, home=home)
    assert result.returncode == 0
    assert result.stdout.strip() == "{}"


def test_save_hook_emits_empty_object_when_config_disables(tmp_path: Path) -> None:
    """~/.mempalace/config.json `hooks.auto_save: false` short-circuits."""
    state = tmp_path / "state"
    home = tmp_path / "home"
    _ensure_palace(home)
    (home / ".mempalace" / "config.json").write_text(
        json.dumps({"hooks": {"auto_save": False}}),
        encoding="utf-8",
    )
    result = _run_hook(SAVE_HOOK, _stop_payload(), state_dir=state, home=home)
    assert result.returncode == 0
    assert result.stdout.strip() == "{}"


def test_save_hook_emits_empty_object_when_fully_idle_false(tmp_path: Path) -> None:
    """fullyIdle=False defers the save; nothing should write to state."""
    state = tmp_path / "state"
    home = tmp_path / "home"
    _ensure_palace(home)
    result = _run_hook(
        SAVE_HOOK,
        _stop_payload(fullyIdle=False),
        state_dir=state,
        home=home,
    )
    assert result.returncode == 0
    assert result.stdout.strip() == "{}"
    # The counter file must NOT exist — we deferred before incrementing.
    counter = state / "antigravity_save_count_test-conv-001"
    assert not counter.exists(), f"counter advanced despite fullyIdle=false: {counter}"


def test_save_hook_emits_empty_object_on_error_termination(tmp_path: Path) -> None:
    """terminationReason=error skips the save."""
    state = tmp_path / "state"
    home = tmp_path / "home"
    _ensure_palace(home)
    result = _run_hook(
        SAVE_HOOK,
        _stop_payload(terminationReason="error", error="model crashed"),
        state_dir=state,
        home=home,
    )
    assert result.returncode == 0
    assert result.stdout.strip() == "{}"


def test_save_hook_emits_empty_object_on_malformed_stdin(tmp_path: Path) -> None:
    """Malformed JSON must not crash the hook — fail-open behaviour."""
    state = tmp_path / "state"
    home = tmp_path / "home"
    _ensure_palace(home)
    result = _run_hook(
        SAVE_HOOK,
        "{not even close to json{",
        state_dir=state,
        home=home,
    )
    assert result.returncode == 0
    assert result.stdout.strip() == "{}"


def test_save_hook_emits_empty_object_on_empty_stdin(tmp_path: Path) -> None:
    """Empty stdin must not crash the hook."""
    state = tmp_path / "state"
    home = tmp_path / "home"
    _ensure_palace(home)
    result = _run_hook(SAVE_HOOK, "", state_dir=state, home=home)
    assert result.returncode == 0
    assert result.stdout.strip() == "{}"


def test_save_hook_never_emits_decision_continue(tmp_path: Path) -> None:
    """The save hook must NEVER emit `{"decision":"continue"}`.

    That output would force Antigravity into an infinite agent
    re-execution loop. Hard rule, separately tested.
    """
    state = tmp_path / "state"
    home = tmp_path / "home"
    _ensure_palace(home)
    result = _run_hook(SAVE_HOOK, _stop_payload(), state_dir=state, home=home)
    assert result.returncode == 0
    # Parse the output so we don't false-match on substring of
    # "Continue thread of work" or similar prose.
    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError:
        pytest.fail(f"save hook emitted non-JSON: {result.stdout!r}")
    assert payload.get("decision") != "continue", (
        f"save hook emitted decision=continue, which would force an infinite "
        f"agent loop. payload={payload!r}"
    )


def test_save_hook_counter_increments_per_fire(tmp_path: Path) -> None:
    """Counter advances on each Stop fire."""
    state = tmp_path / "state"
    home = tmp_path / "home"
    _ensure_palace(home)
    counter_path = state / "antigravity_save_count_test-conv-001"

    for expected in (1, 2, 3):
        result = _run_hook(
            SAVE_HOOK,
            _stop_payload(),
            state_dir=state,
            home=home,
            extra_env={"MEMPAL_SAVE_INTERVAL": "999"},  # high interval -> never trigger save
        )
        assert result.returncode == 0
        assert result.stdout.strip() == "{}"
        assert counter_path.is_file()
        assert counter_path.read_text().strip() == str(expected)


def test_save_hook_floors_zero_save_interval_to_avoid_div_by_zero(tmp_path: Path) -> None:
    """MEMPAL_SAVE_INTERVAL=0 must be floored, never cause `count % 0`."""
    state = tmp_path / "state"
    home = tmp_path / "home"
    _ensure_palace(home)
    result = _run_hook(
        SAVE_HOOK,
        _stop_payload(),
        state_dir=state,
        home=home,
        extra_env={"MEMPAL_SAVE_INTERVAL": "0"},
    )
    # Must NOT crash with bash arithmetic divide-by-zero.
    assert result.returncode == 0, (
        f"save hook crashed on MEMPAL_SAVE_INTERVAL=0:\n"
        f"stdout={result.stdout!r}\nstderr={result.stderr!r}"
    )
    assert result.stdout.strip() == "{}"


def test_save_hook_floors_negative_save_interval(tmp_path: Path) -> None:
    """Negative MEMPAL_SAVE_INTERVAL falls back to default (no crash)."""
    state = tmp_path / "state"
    home = tmp_path / "home"
    _ensure_palace(home)
    result = _run_hook(
        SAVE_HOOK,
        _stop_payload(),
        state_dir=state,
        home=home,
        extra_env={"MEMPAL_SAVE_INTERVAL": "-5"},
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "{}"


def test_save_hook_rejects_traversal_in_transcript_path(tmp_path: Path) -> None:
    """A `..` segment in transcriptPath must be rejected."""
    state = tmp_path / "state"
    home = tmp_path / "home"
    _ensure_palace(home)
    # Set interval to 1 so the modulo gate would normally fire on the
    # first Stop, then prove the path validator stops the spawn.
    result = _run_hook(
        SAVE_HOOK,
        _stop_payload(transcriptPath="/legit/../etc/passwd"),
        state_dir=state,
        home=home,
        extra_env={"MEMPAL_SAVE_INTERVAL": "1"},
    )
    assert result.returncode == 0
    assert result.stdout.strip() == "{}"
    log = state / "antigravity_hook.log"
    assert log.is_file()
    log_body = log.read_text()
    assert "invalid transcriptPath rejected" in log_body or "does not exist" in log_body


def test_save_hook_rejects_non_jsonl_transcript_path(tmp_path: Path) -> None:
    """A transcriptPath ending in something other than .json[l] is rejected."""
    state = tmp_path / "state"
    home = tmp_path / "home"
    _ensure_palace(home)
    result = _run_hook(
        SAVE_HOOK,
        _stop_payload(transcriptPath="/tmp/transcript.txt"),
        state_dir=state,
        home=home,
        extra_env={"MEMPAL_SAVE_INTERVAL": "1"},
    )
    assert result.returncode == 0
    assert result.stdout.strip() == "{}"


def test_save_hook_state_files_are_namespaced_antigravity(tmp_path: Path) -> None:
    """Every state file the save hook touches starts with `antigravity_`.

    The shared state directory is also home to Claude Code, Codex, and
    (in the future) Cursor hook state. Namespacing prevents collisions.
    """
    state = tmp_path / "state"
    home = tmp_path / "home"
    _ensure_palace(home)
    result = _run_hook(
        SAVE_HOOK,
        _stop_payload(),
        state_dir=state,
        home=home,
        extra_env={"MEMPAL_SAVE_INTERVAL": "999"},
    )
    assert result.returncode == 0
    leaks = [p.name for p in state.iterdir() if not p.name.startswith("antigravity_")]
    assert not leaks, f"save hook created non-antigravity-namespaced state files: {leaks}"


def test_save_hook_pending_marker_blocks_concurrent_save(tmp_path: Path) -> None:
    """A fresh pending marker should cause the next save to skip."""
    state = tmp_path / "state"
    home = tmp_path / "home"
    _ensure_palace(home)
    pending = state / "antigravity_pending_test-conv-001"
    state.mkdir(parents=True, exist_ok=True)
    pending.touch()
    # Force the modulo gate to fire by setting interval=1.
    result = _run_hook(
        SAVE_HOOK,
        _stop_payload(),
        state_dir=state,
        home=home,
        extra_env={"MEMPAL_SAVE_INTERVAL": "1"},
    )
    assert result.returncode == 0
    assert result.stdout.strip() == "{}"
    log_body = (state / "antigravity_hook.log").read_text(errors="replace")
    assert "pending save still in flight" in log_body


# ── Wake hook ─────────────────────────────────────────────────────────


def test_wake_hook_emits_empty_object_on_kill_switch(tmp_path: Path) -> None:
    """MEMPAL_DISABLE_HOOK=1 silences the wake hook."""
    state = tmp_path / "state"
    home = tmp_path / "home"
    _ensure_palace(home)
    result = _run_hook(
        WAKE_HOOK,
        _wake_payload(),
        state_dir=state,
        home=home,
        extra_env={"MEMPAL_DISABLE_HOOK": "1"},
    )
    assert result.returncode == 0
    assert result.stdout.strip() == "{}"


@pytest.mark.parametrize("invocation", [0, 2, 5, 100])
def test_wake_hook_emits_empty_when_invocation_num_not_one(tmp_path: Path, invocation: int) -> None:
    """Only invocationNum == 1 triggers injection."""
    state = tmp_path / "state"
    home = tmp_path / "home"
    _ensure_palace(home)
    result = _run_hook(
        WAKE_HOOK,
        _wake_payload(invocationNum=invocation),
        state_dir=state,
        home=home,
    )
    assert result.returncode == 0
    assert result.stdout.strip() == "{}", (
        f"wake hook injected at invocationNum={invocation}: {result.stdout!r}"
    )


def test_wake_hook_loop_guard_prevents_repeat_injection(tmp_path: Path) -> None:
    """A second fire for the same conversationId must skip via the mkdir guard."""
    state = tmp_path / "state"
    home = tmp_path / "home"
    _ensure_palace(home)
    # Pre-create the woke marker dir.
    woke = state / "antigravity_woke_test-conv-001"
    state.mkdir(parents=True, exist_ok=True)
    woke.mkdir()
    result = _run_hook(
        WAKE_HOOK,
        _wake_payload(),
        state_dir=state,
        home=home,
    )
    assert result.returncode == 0
    assert result.stdout.strip() == "{}"
    log_body = (state / "antigravity_hook.log").read_text(errors="replace")
    assert "already woke this conversation" in log_body


def test_wake_hook_never_emits_decision_field(tmp_path: Path) -> None:
    """The wake hook must never emit a `decision` key (that field is Stop-only)."""
    state = tmp_path / "state"
    home = tmp_path / "home"
    _ensure_palace(home)
    result = _run_hook(
        WAKE_HOOK,
        _wake_payload(),
        state_dir=state,
        home=home,
    )
    assert result.returncode == 0
    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError:
        pytest.fail(f"wake hook emitted non-JSON: {result.stdout!r}")
    assert "decision" not in payload, f"wake hook emitted a decision field: {payload!r}"


def test_wake_hook_emits_empty_when_mempalace_missing(tmp_path: Path) -> None:
    """When `mempalace` is not on PATH, the wake hook degrades to `{}`.

    Antigravity's hook framework should never see a stack trace from
    a missing CLI — emit `{}` and let the conversation start without
    injection.
    """
    state = tmp_path / "state"
    home = tmp_path / "home"
    _ensure_palace(home)
    # Strip PATH down to just the bash + python essentials, dropping
    # any directory that might have a `mempalace` binary.
    minimal_path = "/usr/bin:/bin"
    result = _run_hook(
        WAKE_HOOK,
        _wake_payload(),
        state_dir=state,
        home=home,
        extra_env={"PATH": minimal_path},
    )
    assert result.returncode == 0, (
        f"wake hook crashed when mempalace is missing:\n"
        f"stdout={result.stdout!r}\nstderr={result.stderr!r}"
    )
    assert result.stdout.strip() == "{}"


def test_wake_hook_state_files_are_namespaced_antigravity(tmp_path: Path) -> None:
    """Wake hook state files are also namespaced."""
    state = tmp_path / "state"
    home = tmp_path / "home"
    _ensure_palace(home)
    result = _run_hook(WAKE_HOOK, _wake_payload(), state_dir=state, home=home)
    assert result.returncode == 0
    leaks = [p.name for p in state.iterdir() if not p.name.startswith("antigravity_")]
    assert not leaks, leaks


# ── Wing inference ────────────────────────────────────────────────────


def test_wing_inference_picks_first_workspace_path(tmp_path: Path) -> None:
    """Wing is derived from workspacePaths[0]'s leaf directory.

    Antigravity sends an array; the first element is canonical.
    """
    state = tmp_path / "state"
    home = tmp_path / "home"
    _ensure_palace(home)
    # Set interval=1 and a real existing transcript so the save path
    # logs the inferred wing.
    transcript = tmp_path / "transcript.jsonl"
    transcript.write_text("{}\n", encoding="utf-8")
    workspace = tmp_path / "myproj-with-dashes"
    workspace.mkdir()
    result = _run_hook(
        SAVE_HOOK,
        _stop_payload(
            transcriptPath=str(transcript),
            workspacePaths=[str(workspace), "/some/other/workspace"],
        ),
        state_dir=state,
        home=home,
        extra_env={"MEMPAL_SAVE_INTERVAL": "1"},
    )
    assert result.returncode == 0
    log_body = (state / "antigravity_hook.log").read_text(errors="replace")
    # Hyphens become underscores; lowercase.
    assert "wing=wing_myproj_with_dashes" in log_body, log_body


def test_wing_inference_defaults_to_sessions_when_workspace_empty(tmp_path: Path) -> None:
    """An empty workspacePaths array yields wing_sessions."""
    state = tmp_path / "state"
    home = tmp_path / "home"
    _ensure_palace(home)
    transcript = tmp_path / "transcript.jsonl"
    transcript.write_text("{}\n", encoding="utf-8")
    result = _run_hook(
        SAVE_HOOK,
        _stop_payload(
            transcriptPath=str(transcript),
            workspacePaths=[],
        ),
        state_dir=state,
        home=home,
        extra_env={"MEMPAL_SAVE_INTERVAL": "1"},
    )
    assert result.returncode == 0
    log_body = (state / "antigravity_hook.log").read_text(errors="replace")
    assert "wing=wing_sessions" in log_body


# ── Performance budget (soft) ─────────────────────────────────────────


@pytest.mark.skipif(sys.platform == "win32", reason="not relevant on Windows code path")
def test_save_hook_returns_quickly_under_kill_switch(tmp_path: Path) -> None:
    """Under the kill switch the hook should return well under 1s.

    The integration brief budgets hooks at <500ms. We allow a generous
    1500ms here because CI machines can be slow on cold-cache subprocess
    spawn. The point of the test is to fail loudly if a future edit
    introduces a synchronous mempalace import or DB connection.
    """
    import time

    state = tmp_path / "state"
    home = tmp_path / "home"
    _ensure_palace(home)
    start = time.monotonic()
    result = _run_hook(
        SAVE_HOOK,
        _stop_payload(),
        state_dir=state,
        home=home,
        extra_env={"MEMPAL_DISABLE_HOOK": "1"},
    )
    elapsed = time.monotonic() - start
    assert result.returncode == 0
    assert result.stdout.strip() == "{}"
    assert elapsed < 1.5, (
        f"save hook under kill switch took {elapsed:.3f}s; expected < 1.5s. "
        "A regression here usually means a synchronous import / DB connection "
        "is happening before the kill-switch short-circuit."
    )
