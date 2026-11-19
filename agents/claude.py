"""Run Claude Code using the current user's saved login."""

import asyncio
import shutil
from pathlib import Path

from dotenv import load_dotenv
from claude_agent_sdk import (
    ClaudeAgentOptions,
    ResultMessage,
    query,
)

PROJECT_DIR = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_DIR / ".env")


class ClaudeService:
    def __init__(self):
        # Use the same Claude installation available in your terminal.
        self.cli_path = shutil.which("claude")
        self.session_file = PROJECT_DIR / ".claude-whatsapp-session"
        self.session_id = (
            self.session_file.read_text().strip() or None
            if self.session_file.exists()
            else None
        )
        self._lock = asyncio.Lock()

        if not self.cli_path:
            raise RuntimeError(
                "Claude Code was not found. Check that 'claude' works "
                "in the terminal used to start Python."
            )

    async def _reply(self, text: str) -> str:
        options = ClaudeAgentOptions(
            cli_path=self.cli_path,
            cwd=str(PROJECT_DIR),
            add_dirs=[
                str(Path.home() / "Documents"),
                str(Path.home() / "Downloads"),
                str(Path.home() / "Desktop"),
            ],
            system_prompt=(
                "You are my personal assistant accessed through WhatsApp. "
                "Use your tools to inspect files and perform requested tasks. "
                "Explain what you actually completed, and report tool failures."
            ),
            mcp_servers={},
            strict_mcp_config=True,
            # setting_sources=[],
            tools=["Read", "Glob", "Grep", "Write", "Edit", "Bash"],
            allowed_tools=["Read", "Glob", "Grep"],
            permission_mode="acceptEdits",
            max_turns=15,
            resume=self.session_id,
        )

        result = None

        async with asyncio.timeout(120):
            async for message in query(prompt=text, options=options):
                if isinstance(message, ResultMessage):
                    result = message

                    self.session_id = message.session_id
                    temporary = self.session_file.with_suffix(".tmp")
                    temporary.write_text(self.session_id)
                    temporary.replace(self.session_file)

        if result is None:
            raise RuntimeError("Claude returned no final result")

        if result.is_error or result.subtype != "success":
            raise RuntimeError(f"Claude request failed: {result.subtype}")

        return result.result or "Claude returned an empty response."

    async def reply(self, text: str) -> str:
        async with self._lock:
            return await self._reply(text)    