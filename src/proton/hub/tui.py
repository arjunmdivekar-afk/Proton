"""Interactive terminal UI for Proton Model Hub (Hugging Face Transformers)."""

import os
import sys
import time
from typing import Optional, List
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.prompt import Prompt, Confirm
from rich.live import Live

from proton.hub.client import HuggingFaceHubClient, HubModelSummary, HubModelDetails
from proton.hub.hardware import detect_hardware, assess_model_fit
from proton.hub.downloader import ModelDownloader, DownloadProgress, render_progress_bar
from proton.hub.registry import ModelRegistry
from proton.core.config import ConfigManager

console = Console(safe_box=True)


class ModelHubTUI:
    """Terminal user interface for exploring, inspecting, and installing Hugging Face models."""

    def __init__(self):
        self.client = HuggingFaceHubClient()
        self.registry = ModelRegistry()
        self.downloader = ModelDownloader()
        self.hardware = detect_hardware()
        self.config_mgr = ConfigManager()

        self.current_page = 1
        self.page_size = 20
        self.current_query: Optional[str] = None
        self.current_sort = "downloads"
        self.models: List[HubModelSummary] = []
        self.has_next = False

    def run(self) -> None:
        """Launch the main interactive Model Hub loop."""
        self._load_page()

        while True:
            self._render_catalog()
            action = Prompt.ask(
                "[bold cyan]Hub Action[/bold cyan] ([bold]1-20[/bold] Select, [bold]/[/bold] Search, [bold]N[/bold] Next, [bold]P[/bold] Prev, [bold]L[/bold] Local/Installed, [bold]H[/bold] Hardware, [bold]Q[/bold] Quit)",
                default="Q",
            ).strip()

            if not action:
                continue

            act_lower = action.lower()
            if act_lower in ("q", "quit", "exit"):
                console.print("[dim]Exiting Model Hub.[/dim]\n")
                break
            elif act_lower in ("n", "next"):
                if self.has_next:
                    self.current_page += 1
                    self._load_page()
                else:
                    console.print("[yellow]No more pages.[/yellow]")
                    time.sleep(1)
            elif act_lower in ("p", "prev", "previous"):
                if self.current_page > 1:
                    self.current_page -= 1
                    self._load_page()
                else:
                    console.print("[yellow]Already on first page.[/yellow]")
                    time.sleep(1)
            elif act_lower.startswith("/") or act_lower == "s" or act_lower == "search":
                q = Prompt.ask("[bold cyan]Enter Search Keyword / Model Name[/bold cyan]").strip()
                self.current_query = q if q else None
                self.current_page = 1
                self._load_page()
            elif act_lower in ("l", "local", "installed"):
                self._show_installed_models()
            elif act_lower in ("h", "hw", "hardware"):
                self._show_hardware_profile()
            elif action.isdigit():
                idx = int(action) - 1
                if 0 <= idx < len(self.models):
                    selected = self.models[idx]
                    self._view_and_install_model(selected.id)
                else:
                    console.print(f"[red]Invalid selection: {action}[/red]")
                    time.sleep(1)
            else:
                # Direct search or model ID input
                self._view_and_install_model(action)

    def _load_page(self) -> None:
        """Fetch models for current page."""
        with console.status("[bold cyan]Querying Hugging Face Transformers models...[/bold cyan]"):
            self.models, self.has_next, self.current_page = self.client.search_models(
                query=self.current_query,
                page=self.current_page,
                page_size=self.page_size,
                sort=self.current_sort,
            )

    def _render_catalog(self) -> None:
        """Render the 20-model catalog table."""
        console.clear()

        # Hardware summary line
        hw = self.hardware
        gpu_info = f"GPU: [bold green]{hw.cuda_device_name}[/bold green] ({hw.cuda_vram_gb} GB VRAM)" if hw.has_cuda else "GPU: [yellow]None (CPU Mode)[/yellow]"
        ram_info = f"RAM: [bold cyan]{hw.available_ram_gb} GB free[/bold cyan] / {hw.total_ram_gb} GB"
        disk_info = f"Disk: [bold cyan]{hw.disk_free_gb} GB free[/bold cyan]"

        header_panel = Panel(
            f"[bold bright_white]🤗 Hugging Face Transformers Model Hub[/bold bright_white]\n"
            f"[dim]{gpu_info}  •  {ram_info}  •  {disk_info}[/dim]\n"
            f"[dim]Search filter: [bold yellow]{self.current_query or 'All Trending Text Generation'}[/bold yellow]  •  Page [bold]{self.current_page}[/bold][/dim]",
            title="[bold cyan]⚛️ PROTON MODEL HUB v2.4.4[/bold cyan]",
            border_style="cyan",
        )
        console.print(header_panel)

        if not self.models:
            console.print(Panel("[yellow]No matching models found. Try another search keyword.[/yellow]", border_style="yellow"))
            return

        table = Table(show_header=True, header_style="bold cyan", expand=True)
        table.add_column("#", style="bold yellow", width=3, justify="right")
        table.add_column("Model ID / Name", style="bold bright_white", width=32)
        table.add_column("Author", style="dim", width=12)
        table.add_column("Params", style="bold green", width=7, justify="center")
        table.add_column("Size", style="cyan", width=8, justify="right")
        table.add_column("Downloads", style="dim", width=9, justify="right")
        table.add_column("Likes", style="dim", width=6, justify="right")
        table.add_column("Format", style="dim", width=9)
        table.add_column("License", style="dim", width=10)
        table.add_column("Status", style="bold", width=9)

        installed_ids = {m.id for m in self.registry.list_installed()}
        default_model = self.registry.get_default_model()
        default_id = default_model.id if default_model else None

        for idx, m in enumerate(self.models, 1):
            status = "[bold green]✓ Installed[/bold green]" if m.id in installed_ids else "[dim]Available[/dim]"
            if m.id == default_id:
                status = "[bold magenta]★ Default[/bold magenta]"

            # Format downloads
            dl_str = f"{m.downloads // 1000}k" if m.downloads >= 1000 else str(m.downloads)
            like_str = f"{m.likes // 1000}k" if m.likes >= 1000 else str(m.likes)
            size_str = f"{m.estimated_size_gb:.1f} GB" if m.estimated_size_gb > 0 else "~2.5 GB"

            table.add_row(
                str(idx),
                m.name[:31],
                m.author[:11],
                m.parameters_display,
                size_str,
                dl_str,
                like_str,
                m.quantization[:8],
                m.license[:9],
                status,
            )

        console.print(table)
        console.print()

    def _show_hardware_profile(self) -> None:
        """Display hardware advisor and memory capacity breakdown."""
        hw = detect_hardware()
        console.clear()

        table = Table(title="System Hardware Specifications & AI Readiness", show_header=True, header_style="bold cyan")
        table.add_column("Component", style="bold yellow", width=22)
        table.add_column("Specification", style="bold bright_white", width=48)

        table.add_row("Operating System", hw.os_name)
        table.add_row("CPU Architecture", f"{hw.cpu_arch} ({hw.cpu_count_physical} Cores, {hw.cpu_count_logical} Threads)")
        table.add_row("System RAM", f"{hw.available_ram_gb} GB Available / {hw.total_ram_gb} GB Total")
        table.add_row("Free Disk Space", f"{hw.disk_free_gb} GB Free")

        if hw.has_cuda:
            table.add_row("NVIDIA GPU", f"{hw.cuda_device_name} ({hw.cuda_vram_gb} GB VRAM)")
            table.add_row("Hardware Acceleration", "[bold green]CUDA 12+ (Full GPU Tensor Acceleration)[/bold green]")
        elif hw.has_mps:
            table.add_row("Apple Silicon GPU", "[bold green]Apple MPS Metal Acceleration Active[/bold green]")
        else:
            table.add_row("Hardware Acceleration", "[yellow]CPU Only (AVX/AMX In-Process Execution)[/yellow]")

        table.add_row("Recommended Runtime", f"[bold cyan]{hw.recommended_device.upper()}[/bold cyan]")

        console.print(table)
        console.print()

        # Model fit tier matrix
        tiers_table = Table(title="Model Parameter Fit Matrix", show_header=True, header_style="bold cyan")
        tiers_table.add_column("Model Scale", style="bold yellow", width=14)
        tiers_table.add_column("RAM / VRAM Req", style="dim", width=14)
        tiers_table.add_column("Compatibility Verdict", style="bold", width=42)

        for p_val, label in [(1.2, "1B - 1.5B"), (3.0, "3B"), (7.0, "7B - 8B"), (14.0, "14B"), (70.0, "70B")]:
            verdict = assess_model_fit(p_val, hardware=hw)
            fit_text = f"[green]✓ Fits — {verdict.performance_tier}[/green]" if verdict.fits else f"[red]✗ May OOM — {verdict.warning_message}[/red]"
            tiers_table.add_row(label, f"~{verdict.estimated_ram_required_gb:.1f} GB", fit_text)

        console.print(tiers_table)
        console.print()
        Prompt.ask("[dim]Press ENTER to return to Model Hub[/dim]")

    def _show_installed_models(self) -> None:
        """List and manage locally installed models."""
        installed = self.registry.list_installed()
        console.clear()

        if not installed:
            console.print(Panel("[yellow]No models currently installed. Search or select a model from the hub to install.[/yellow]", border_style="yellow"))
            Prompt.ask("\n[dim]Press ENTER to return[/dim]")
            return

        table = Table(title="Locally Installed Transformers Models", show_header=True, header_style="bold cyan")
        table.add_column("#", style="bold yellow", width=3)
        table.add_column("Model ID", style="bold bright_white", width=34)
        table.add_column("Params", style="bold green", width=8)
        table.add_column("Size", style="cyan", width=8)
        table.add_column("Installed Path", style="dim", width=30)
        table.add_column("Default", style="bold", width=9)

        for idx, m in enumerate(installed, 1):
            is_def = "[bold magenta]★ Default[/bold magenta]" if m.is_default else "[dim]—[/dim]"
            table.add_row(
                str(idx),
                m.id,
                m.parameters_display,
                f"{m.size_gb:.1f} GB",
                str(m.local_path)[-28:],
                is_def,
            )

        console.print(table)
        console.print()
        sel = Prompt.ask("[bold cyan]Action[/bold cyan] ([bold]1-N[/bold] Set Default / Remove, [bold]Q[/bold] Back)", default="Q").strip()

        if sel.isdigit():
            idx = int(sel) - 1
            if 0 <= idx < len(installed):
                chosen = installed[idx]
                act = Prompt.ask(
                    f"Selected: [bold]{chosen.id}[/bold]\n([bold]D[/bold] Set as Default, [bold]R[/bold] Remove/Delete, [bold]Q[/bold] Cancel)",
                    default="D",
                ).strip().lower()

                if act == "d":
                    self.registry.set_as_proton_default(chosen.id)
                    console.print(f"[bold green]✓ Set '{chosen.id}' as Proton's default Transformers model![/bold green]")
                    time.sleep(1.5)
                elif act == "r":
                    if Confirm.ask(f"Are you sure you want to remove '{chosen.id}' and free disk space?"):
                        import shutil
                        if os.path.exists(chosen.local_path):
                            shutil.rmtree(chosen.local_path, ignore_errors=True)
                        self.registry.unregister(chosen.id)
                        console.print(f"[green]✓ Removed '{chosen.id}'.[/green]")
                        time.sleep(1.5)

    def _view_and_install_model(self, model_id: str) -> None:
        """Fetch model details, display full metadata screen, and offer install."""
        console.clear()
        with console.status(f"[bold cyan]Fetching details for '{model_id}' from Hugging Face...[/bold cyan]"):
            details = self.client.get_model_details(model_id)

        if not details:
            console.print(Panel(f"[red]Could not retrieve model metadata for '{model_id}'. Verify the model ID exists on Hugging Face.[/red]", border_style="red"))
            Prompt.ask("\n[dim]Press ENTER to return[/dim]")
            return

        # Assess hardware fit
        verdict = assess_model_fit(details.parameters_billions, hardware=self.hardware)

        # Build detail view
        console.clear()
        meta_table = Table(show_header=False, expand=True)
        meta_table.add_column("Key", style="bold cyan", width=22)
        meta_table.add_column("Value", style="bold bright_white")

        meta_table.add_row("Model Repository", details.id)
        meta_table.add_row("Author / Org", details.author)
        meta_table.add_row("Estimated Parameters", f"[bold green]{details.parameters_display}[/bold green]")
        meta_table.add_row("Download Size", f"[cyan]{details.estimated_size_gb:.1f} GB[/cyan] ({len(details.siblings_files)} repository files)")
        meta_table.add_row("Downloads / Likes", f"{details.downloads:,} downloads  •  {details.likes:,} likes")
        meta_table.add_row("Architecture / Task", f"{details.architecture}  •  {details.task}")
        meta_table.add_row("Weight Format", details.quantization)
        meta_table.add_row("License", details.license)
        meta_table.add_row(
            "Hardware Assessment",
            f"[bold green]✓ {verdict.performance_tier}[/bold green]" if verdict.fits else f"[bold yellow]⚠️ {verdict.warning_message}[/bold yellow]",
        )

        if details.requires_remote_code:
            meta_table.add_row("Remote Code Security", "[bold red]⚠️ Requires trust_remote_code=True[/bold red]")
        else:
            meta_table.add_row("Remote Code Security", "[bold green]✓ Safe (Standard Transformers Architecture)[/bold green]")

        is_already_installed = self.registry.is_installed(model_id)
        status_badge = "[bold green]✓ ALREADY INSTALLED[/bold green]" if is_already_installed else "[bold yellow]NOT INSTALLED[/bold yellow]"

        console.print(
            Panel(
                meta_table,
                title=f"[bold cyan]🤗 Model Details: {details.id}[/bold cyan]  {status_badge}",
                border_style="cyan",
            )
        )

        if is_already_installed:
            rec = self.registry.get_model(model_id)
            is_def = rec.is_default if rec else False
            prompt_str = "[ENTER] " + ("(Already Default)" if is_def else "Set as Default") + ", [R] Run, [B] Benchmark, [Q] Back"
            act = Prompt.ask(f"[bold cyan]Select Action[/bold cyan] ({prompt_str})", default="ENTER").strip().lower()
            if act in ("enter", ""):
                self.registry.set_as_proton_default(model_id)
                console.print(f"[bold green]✓ Set '{model_id}' as Proton's default model![/bold green]")
                time.sleep(1.5)
            return

        # Prompt for installation
        console.print()
        if not Confirm.ask(f"[bold bright_white]Install '{details.id}' ({details.estimated_size_gb:.1f} GB) now?[/bold bright_white]", default=True):
            return

        # Remote code check
        trust_remote = False
        if details.requires_remote_code:
            console.print("\n[bold yellow]⚠️ SECURITY WARNING: This model uses custom model code outside the standard Transformers library.[/bold yellow]")
            if not Confirm.ask("Do you explicitly approve running custom remote code for this model?", default=False):
                console.print("[red]Installation cancelled for security.[/red]")
                time.sleep(1.5)
                return
            trust_remote = True

        # Execute real-time progress download
        self._execute_live_download(details, trust_remote)

    def _execute_live_download(self, details: HubModelDetails, trust_remote_code: bool) -> None:
        """Run the actual snapshot download with live rendering of real progress."""
        console.clear()
        console.print(f"[bold cyan]⬇️ Downloading '{details.id}'...[/bold cyan]\n")

        latest_progress = DownloadProgress(
            percentage=0.0,
            downloaded_display="0.0 GB",
            total_display=f"{details.estimated_size_gb:.1f} GB",
            speed_mb_s=0.0,
            eta_display="Connecting...",
            completed_files=0,
            total_files=len(details.siblings_files) or 1,
            current_file="Initializing repository stream...",
            status="Connecting",
            progress_bar=render_progress_bar(0.0),
        )

        def make_progress_panel(p: DownloadProgress) -> Panel:
            lines = [
                f"[bold bright_white]{p.progress_bar}[/bold bright_white]\n",
                f"[bold cyan]{p.percentage:.1f}%[/bold cyan]",
                f"[bold white]{p.downloaded_display}[/bold white] / [dim]{p.total_display}[/dim]",
                f"Speed: [bold green]{p.speed_mb_s:.1f} MB/s[/bold green]",
                f"ETA: [yellow]{p.eta_display}[/yellow]",
                f"Files: [bold white]{p.completed_files} / {p.total_files}[/bold white]",
                f"Current file: [dim]{p.current_file}[/dim]",
                f"Status: [bold cyan]{p.status}[/bold cyan]",
            ]
            return Panel(
                "\n".join(lines),
                title=f"[bold cyan]📥 Installing {details.id}[/bold cyan]",
                subtitle="[dim]Press Ctrl+C to cancel download[/dim]",
                border_style="cyan",
            )

        with Live(make_progress_panel(latest_progress), refresh_per_second=4, console=console) as live:
            def on_progress(p: DownloadProgress):
                nonlocal latest_progress
                latest_progress = p
                live.update(make_progress_panel(p))

            try:
                final_path = self.downloader.download_model(
                    model_id=details.id,
                    progress_callback=on_progress,
                )
            except InterruptedError:
                console.print("\n[yellow]⚠️ Download cancelled by user. Partial files cleaned up.[/yellow]")
                time.sleep(2)
                return
            except Exception as e:
                console.print(f"\n[red]✗ Download failed: {str(e)}[/red]")
                Prompt.ask("\n[dim]Press ENTER to continue[/dim]")
                return

        # Register installed model
        record = self.registry.register(
            model_id=details.id,
            local_path=final_path,
            total_bytes=latest_progress.total_bytes,
            parameters_display=details.parameters_display,
            license=details.license,
            requires_remote_code=trust_remote_code,
            is_default=True,
        )

        # Show success & post-installation menu
        console.clear()
        success_text = (
            f"[bold green]✓ Model installed successfully![/bold green]\n\n"
            f"Repository: [bold bright_white]{details.id}[/bold bright_white]\n"
            f"Local Path: [dim]{record.local_path}[/dim]\n"
            f"Size: [cyan]{record.size_gb:.1f} GB[/cyan]\n"
            f"Parameters: [green]{record.parameters_display}[/green]\n"
        )
        console.print(Panel(success_text, title="[bold green]⚛️ Installation Complete[/bold green]", border_style="green"))

        console.print(
            "[bold bright_white][ENTER][/bold bright_white] Set as Default  •  "
            "[bold bright_white][B][/bold bright_white] Benchmark  •  "
            "[bold bright_white][R][/bold bright_white] Run Model  •  "
            "[bold bright_white][Q][/bold bright_white] Back\n"
        )

        post_action = Prompt.ask("[bold cyan]Choose Action[/bold cyan]", default="ENTER").strip().upper()

        if post_action in ("ENTER", "", "D", "DEFAULT"):
            self.registry.set_as_proton_default(details.id)
            # Ensure Transformers is active connection
            from proton.connection.manager import ConnectionManager
            conn_mgr = ConnectionManager()
            conn_mgr.set_active_connection("transformers")
            console.print(f"\n[bold green]★ '{details.id}' is now Proton's default model and Transformers is active provider![/bold green]")
            time.sleep(2)
        elif post_action == "B":
            console.print("\n[bold cyan]Launching Model Benchmark...[/bold cyan]")
            import asyncio
            from proton.benchmark.runner import BenchmarkRunner
            runner = BenchmarkRunner(quick=True)
            asyncio.run(runner.run_benchmark())
            Prompt.ask("\n[dim]Press ENTER to continue[/dim]")
        elif post_action == "R":
            console.print(f"\n[bold green]Active model set to '{details.id}'. Launching Proton REPL...[/bold green]")
            self.registry.set_as_proton_default(details.id)
            time.sleep(1)
