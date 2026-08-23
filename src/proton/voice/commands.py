"""Voice Commands Parser and Dispatcher for Proton Voice Mode."""

import re
from typing import Optional, Dict, Any, Tuple
from pydantic import BaseModel
from proton.core.config import ConfigManager
from proton.connection.manager import ConnectionManager


class VoiceCommandResult(BaseModel):
    """Result of voice command execution."""
    is_command: bool = False
    command_name: Optional[str] = None
    feedback_speech: Optional[str] = None
    should_exit: bool = False
    should_interrupt: bool = False
    action_data: Dict[str, Any] = {}


class VoiceCommandDispatcher:
    """Matches spoken text against system voice commands."""

    def __init__(self, config_manager: Optional[ConfigManager] = None):
        self.config_mgr = config_manager or ConfigManager()
        self.conn_mgr = ConnectionManager(self.config_mgr)

    def dispatch(self, spoken_text: str) -> VoiceCommandResult:
        """Parse spoken input and execute system commands if matched."""
        if not spoken_text:
            return VoiceCommandResult()

        text = spoken_text.lower().strip()

        # 1. Stop / Interruption Commands
        if text in ("stop", "cancel", "shut up", "be quiet", "pause", "stop speaking", "hush"):
            return VoiceCommandResult(
                is_command=True,
                command_name="stop",
                feedback_speech="Stopped.",
                should_interrupt=True,
            )

        # 2. Exit Voice Mode
        if text in ("exit", "exit voice", "quit voice", "goodbye", "close voice", "bye bye", "bye"):
            return VoiceCommandResult(
                is_command=True,
                command_name="exit",
                feedback_speech="Exiting voice mode. Have a great day!",
                should_exit=True,
            )

        # 3. Clear History / Session Reset
        if "clear history" in text or "reset chat" in text or "clear context" in text:
            return VoiceCommandResult(
                is_command=True,
                command_name="clear_history",
                feedback_speech="Conversation history cleared.",
                action_data={"action": "reset_session"},
            )

        # 4. Status Check
        if text in ("status", "server status", "what is your status", "check status"):
            active_conn = self.conn_mgr.get_active_connection()
            active_model = self.config_mgr.config.active_model or "default"
            conn_name = active_conn.name if active_conn else "No active connection"
            return VoiceCommandResult(
                is_command=True,
                command_name="status",
                feedback_speech=f"Proton is online. Active provider is {conn_name}, using model {active_model}.",
            )

        # 5. Switch Model: "switch model to <name>" / "change model to <name>"
        match_model = re.search(r'(?:switch|change|set)\s+model\s+(?:to\s+)?([a-zA-Z0-9_\-\.\/]+)', text)
        if match_model:
            model_target = match_model.group(1).strip()
            self.config_mgr.set_active_model(model_target)
            return VoiceCommandResult(
                is_command=True,
                command_name="switch_model",
                feedback_speech=f"Switched active model to {model_target}.",
                action_data={"model": model_target},
            )

        # 6. Switch Provider: "switch provider to <name>"
        match_provider = re.search(r'(?:switch|change|set)\s+(?:provider|connection)\s+(?:to\s+)?([a-zA-Z0-9_\-\.\s]+)', text)
        if match_provider:
            prov_target = match_provider.group(1).strip().lower()
            conns = self.conn_mgr.list_connections()
            matched_conn = None
            for c in conns:
                if prov_target in c.name.lower() or prov_target in c.id.lower() or prov_target in c.provider.value.lower():
                    matched_conn = c
                    break

            if matched_conn:
                self.config_mgr.set_active_connection(matched_conn.id)
                return VoiceCommandResult(
                    is_command=True,
                    command_name="switch_provider",
                    feedback_speech=f"Switched active connection to {matched_conn.name}.",
                    action_data={"connection_id": matched_conn.id},
                )
            else:
                return VoiceCommandResult(
                    is_command=True,
                    command_name="switch_provider_failed",
                    feedback_speech=f"Could not find a configured provider matching {prov_target}.",
                )

        return VoiceCommandResult(is_command=False)
