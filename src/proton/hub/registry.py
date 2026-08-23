"""Local model registry for managing installed Transformers models."""

import os
import re
import json
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field

from proton.core.config import get_proton_home, ConfigManager


class InstalledModelRecord(BaseModel):
    """Metadata record of a locally installed model."""
    id: str
    name: str
    author: str
    local_path: str
    total_bytes: int = 0
    size_gb: float = 0.0
    parameters_display: str = "Unknown"
    license: str = "Unknown"
    installed_at: str = Field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    is_default: bool = False
    task: str = "text-generation"
    requires_remote_code: bool = False
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ModelRegistry:
    """Manages tracking, persistence, and default selection of installed models."""

    def __init__(self, root_dir: Optional[Path] = None, registry_file: Optional[Path] = None):
        self.root_dir = root_dir or (registry_file.parent if registry_file else (get_proton_home() / "models"))
        self.root_dir.mkdir(parents=True, exist_ok=True)
        self.registry_file = registry_file or (self.root_dir / "registry.json")

    def _scan_cache_dir(self, records: Dict[str, InstalledModelRecord]) -> bool:
        """Scan cache directory for downloaded models and register any untracked ones."""
        cache_dir = self.root_dir / "cache"
        if not cache_dir.exists():
            return False

        changed = False
        for folder in cache_dir.iterdir():
            if not folder.is_dir():
                continue

            folder_name = folder.name
            if "--" in folder_name:
                parts = folder_name.split("--", 1)
                model_id = f"{parts[0]}/{parts[1]}"
                author = parts[0]
                name = parts[1]
            else:
                model_id = folder_name
                author = "Local"
                name = folder_name

            if model_id not in records:
                # Calculate size on disk
                total_bytes = 0
                for root, _, fnames in os.walk(folder):
                    for fn in fnames:
                        fp = Path(root) / fn
                        try:
                            total_bytes += fp.stat().st_size
                        except Exception:
                            pass

                # If folder has content (> 100KB), auto-register it
                if total_bytes > 100 * 1024:
                    # Estimate parameters display
                    param_disp = "Unknown"
                    m = re.search(r"[-_]([0-9]+(?:\.[0-9]+)?)[bB](?:[-_]|$)", model_id)
                    if m:
                        param_disp = f"{m.group(1)}B"

                    size_gb = round(total_bytes / (1024 ** 3), 2)
                    records[model_id] = InstalledModelRecord(
                        id=model_id,
                        name=name,
                        author=author,
                        local_path=str(folder.resolve()),
                        total_bytes=total_bytes,
                        size_gb=size_gb,
                        parameters_display=param_disp,
                        installed_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        is_default=(len(records) == 0),
                    )
                    changed = True

        return changed

    def _load(self) -> Dict[str, InstalledModelRecord]:
        records: Dict[str, InstalledModelRecord] = {}
        if self.registry_file.exists():
            try:
                data = json.loads(self.registry_file.read_text(encoding="utf-8"))
                records = {k: InstalledModelRecord(**v) for k, v in data.items()}
            except Exception:
                records = {}

        # Reconcile cache
        if self._scan_cache_dir(records):
            self._save(records)

        return records

    def _save(self, records: Dict[str, InstalledModelRecord]) -> None:
        data = {k: v.model_dump(mode="json") for k, v in records.items()}
        self.registry_file.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def list_installed(self) -> List[InstalledModelRecord]:
        """List all locally installed and registered models."""
        records = self._load()
        return list(records.values())

    def get_model(self, model_id: str) -> Optional[InstalledModelRecord]:
        """Get record for a specific model ID."""
        records = self._load()
        return records.get(model_id)

    def is_installed(self, model_id: str) -> bool:
        """Check if model is registered and directory exists."""
        rec = self.get_model(model_id)
        if not rec:
            return False
        return Path(rec.local_path).exists()

    def register(
        self,
        model_id: str,
        local_path: Path,
        total_bytes: int = 0,
        parameters_display: str = "Unknown",
        license: str = "Unknown",
        requires_remote_code: bool = False,
        is_default: bool = False,
    ) -> InstalledModelRecord:
        """Register newly installed model."""
        records = self._load()
        parts = model_id.split("/", 1)
        author = parts[0] if len(parts) > 1 else "Local"
        name = parts[1] if len(parts) > 1 else parts[0]

        size_gb = round(total_bytes / (1024 ** 3), 2) if total_bytes > 0 else 0.0

        if is_default:
            for r in records.values():
                r.is_default = False

        record = InstalledModelRecord(
            id=model_id,
            name=name,
            author=author,
            local_path=str(local_path.resolve()),
            total_bytes=total_bytes,
            size_gb=size_gb,
            parameters_display=parameters_display,
            license=license,
            installed_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            is_default=is_default,
            requires_remote_code=requires_remote_code,
        )

        records[model_id] = record
        self._save(records)

        if is_default:
            self.set_as_proton_default(model_id)

        return record

    def unregister(self, model_id: str) -> bool:
        """Remove model from registry."""
        records = self._load()
        if model_id in records:
            del records[model_id]
            self._save(records)
            return True
        return False

    def set_as_proton_default(self, model_id: str) -> bool:
        """
        Mark model as default in registry, update Proton ConfigManager to use
        Transformers as the default provider, and persist permanently.
        """
        records = self._load()
        if model_id not in records:
            return False

        for k, r in records.items():
            r.is_default = (k == model_id)
        self._save(records)

        # Update Proton system configuration permanently
        config_mgr = ConfigManager()
        config_mgr.set_active_model(model_id)
        config_mgr.set_active_connection("transformers")
        return True

    def get_default_model(self) -> Optional[InstalledModelRecord]:
        """Get the current default installed model."""
        records = self._load()
        for r in records.values():
            if r.is_default:
                return r
        if records:
            return next(iter(records.values()))
        return None
