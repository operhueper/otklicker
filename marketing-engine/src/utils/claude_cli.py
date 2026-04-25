"""Claude Code CLI wrapper.

Calls the `claude` CLI binary to generate content using the user's
Claude subscription instead of the Anthropic API.

Architecture:
  1. Build combined prompt from system + user parts
  2. Call `claude -p "<prompt>"` via subprocess
  3. Parse stdout as the response
  4. Retry up to 3 times on failure
"""

from __future__ import annotations

import asyncio
import shlex
import time
from typing import Optional

import structlog

logger = structlog.get_logger(__name__)

_DEFAULT_TIMEOUT = 120  # seconds
_MAX_RETRIES = 3
_RETRY_DELAY = 5  # seconds between retries


async def generate(
    system_prompt: str,
    user_prompt: str,
    max_tokens: int = 4096,
    claude_cli_path: str = "claude",
    timeout: int = _DEFAULT_TIMEOUT,
    allowed_tools: Optional[str] = None,
    model: str = "haiku",
) -> str:
    """Generate text via Claude Code CLI.

    Args:
        system_prompt: Role / context instructions for Claude.
        user_prompt: The actual user request.
        max_tokens: Hint for response length (not enforced by CLI, used as note in prompt).
        claude_cli_path: Path to `claude` binary (default: resolved from PATH).
        timeout: Subprocess timeout in seconds.
        allowed_tools: Optional tool pattern to allow (e.g. "mcp__pencil__*").

    Returns:
        Generated text from Claude.

    Raises:
        RuntimeError: After exhausting all retries.
    """
    combined_prompt = _build_prompt(system_prompt, user_prompt, max_tokens)

    last_error: Optional[Exception] = None
    for attempt in range(1, _MAX_RETRIES + 1):
        try:
            logger.debug(
                "claude_cli.generate.attempt",
                attempt=attempt,
                prompt_length=len(combined_prompt),
                model=model,
            )
            result = await _run_cli(
                combined_prompt, claude_cli_path, timeout,
                allowed_tools=allowed_tools,
                model=model,
            )
            logger.debug(
                "claude_cli.generate.success",
                attempt=attempt,
                response_length=len(result),
            )
            return result
        except Exception as exc:
            last_error = exc
            logger.warning(
                "claude_cli.generate.failed",
                attempt=attempt,
                error=str(exc),
            )
            if attempt < _MAX_RETRIES:
                await asyncio.sleep(_RETRY_DELAY)

    raise RuntimeError(
        f"Claude CLI failed after {_MAX_RETRIES} attempts. Last error: {last_error}"
    ) from last_error


def _build_prompt(system_prompt: str, user_prompt: str, max_tokens: int) -> str:
    """Combine system and user prompts into a single CLI prompt string."""
    parts = []

    if system_prompt.strip():
        parts.append(f"<system>\n{system_prompt.strip()}\n</system>")

    parts.append(user_prompt.strip())

    if max_tokens and max_tokens < 2000:
        parts.append(f"\n[Ограничение: ответ не более {max_tokens} токенов]")

    return "\n\n".join(parts)


async def _run_cli(
    prompt: str,
    claude_cli_path: str,
    timeout: int,
    allowed_tools: Optional[str] = None,
    model: str = "haiku",
) -> str:
    """Execute the claude CLI process and capture output."""
    # -p passes prompt directly in non-interactive mode
    cmd = [claude_cli_path, "-p", prompt, "--model", model]

    if allowed_tools:
        cmd.extend(["--allowedTools", allowed_tools])

    start_time = time.monotonic()
    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        try:
            stdout_bytes, stderr_bytes = await asyncio.wait_for(
                proc.communicate(), timeout=timeout
            )
        except asyncio.TimeoutError:
            proc.kill()
            await proc.communicate()
            raise TimeoutError(
                f"Claude CLI timed out after {timeout}s"
            )

        elapsed = time.monotonic() - start_time
        stdout = stdout_bytes.decode("utf-8", errors="replace").strip()
        stderr = stderr_bytes.decode("utf-8", errors="replace").strip()

        logger.debug(
            "claude_cli.process.finished",
            returncode=proc.returncode,
            elapsed_seconds=round(elapsed, 2),
            stdout_length=len(stdout),
            stderr_preview=stderr[:200] if stderr else "",
        )

        if proc.returncode != 0:
            raise RuntimeError(
                f"Claude CLI exited with code {proc.returncode}. "
                f"stderr: {stderr[:500]}"
            )

        if not stdout:
            raise ValueError("Claude CLI returned empty output")

        return stdout

    except (OSError, FileNotFoundError) as exc:
        raise RuntimeError(
            f"Cannot find claude CLI at '{claude_cli_path}'. "
            "Install Claude Code or set CLAUDE_CLI_PATH."
        ) from exc
