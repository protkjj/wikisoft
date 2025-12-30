#!/usr/bin/env python3
import os
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any

MAC_CODE_USER = Path.home() / "Library" / "Application Support" / "Code" / "User"
GLOBAL_EMPTY_SESSIONS = MAC_CODE_USER / "globalStorage" / "emptyWindowChatSessions"
WORKSPACE_STORAGE = MAC_CODE_USER / "workspaceStorage"

def _read_json(path: Path) -> Dict[str, Any]:
    try:
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        return {"_error": f"Failed to read {path}: {e}"}

def _collect_session_files() -> List[Path]:
    files: List[Path] = []
    # Global empty-window chat sessions
    if GLOBAL_EMPTY_SESSIONS.exists():
        files.extend(sorted(GLOBAL_EMPTY_SESSIONS.glob("*.json")))
    # Workspace chat sessions (workspaceStorage/*/chatSessions/*.json)
    if WORKSPACE_STORAGE.exists():
        for ws in WORKSPACE_STORAGE.iterdir():
            chat_dir = ws / "chatSessions"
            if chat_dir.is_dir():
                files.extend(sorted(chat_dir.glob("*.json")))
    return files

def _ensure_output_dir() -> Path:
    dest = Path.home() / "Desktop" / "copilot_chat_backup" / datetime.now().strftime("%Y-%m-%d_%H%M%S")
    dest.mkdir(parents=True, exist_ok=True)
    return dest

def _message_text(message: Dict[str, Any]) -> str:
    # Prefer direct text
    text = message.get("text")
    if isinstance(text, str) and text.strip():
        return text.strip()
    # Fallback to parts aggregation
    parts = message.get("parts")
    if isinstance(parts, list):
        acc = []
        for p in parts:
            t = p.get("text")
            if isinstance(t, str) and t:
                acc.append(t)
        if acc:
            return "\n".join(acc).strip()
    return ""

def _extract_conversation(session: Dict[str, Any]) -> List[str]:
    lines: List[str] = []
    requests = session.get("requests", [])
    for req in requests:
        msg = req.get("message", {})
        user_text = _message_text(msg)
        if user_text:
            lines.append(f"User: {user_text}")
        # Responses can be a list of mixed events; capture string values
        response = req.get("response", [])
        if isinstance(response, list):
            for item in response:
                val = item.get("value")
                if isinstance(val, str) and val.strip():
                    # Collapse newlines a bit for readability
                    lines.append(f"Copilot: {val.strip()}")
    return lines

def export_sessions() -> int:
    session_files = _collect_session_files()
    if not session_files:
        print("No Copilot chat session files found.")
        return 0
    out_dir = _ensure_output_dir()
    count = 0
    for path in session_files:
        data = _read_json(path)
        # Basic metadata
        agent = data.get("responderUsername") or data.get("agent", {}).get("name") or "GitHub Copilot"
        initial_loc = data.get("initialLocation")
        source = "workspace"
        if path.parent.name == "emptyWindowChatSessions":
            source = "emptyWindow"
        ws_id = path.parent.parent.name if source == "workspace" else "global"
        # Build markdown
        conv = _extract_conversation(data)
        md_lines = [
            f"# Copilot Chat Session",
            f"- File: {path}",
            f"- Source: {source}",
            f"- WorkspaceId: {ws_id}",
            f"- Agent: {agent}",
            f"- InitialLocation: {initial_loc}",
            "",
            "## Transcript",
        ]
        md_lines.extend(conv if conv else ["(No transcript content extracted)"])
        # Output filename
        out_name = f"{path.stem}.md"
        out_path = out_dir / out_name
        try:
            out_path.write_text("\n".join(md_lines), encoding="utf-8")
            count += 1
        except Exception as e:
            print(f"Failed to write {out_path}: {e}")
    print(f"Exported {count} sessions to {out_dir}")
    return count

if __name__ == "__main__":
    export_sessions()
