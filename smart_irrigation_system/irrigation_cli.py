from rich.live import Live
from rich.table import Table
from rich.console import Console
from rich.panel import Panel
from rich.align import Align
from rich.text import Text
import threading
import time, logging, datetime
from typing import Optional

from smart_irrigation_system.irrigation_controller import IrrigationController
from smart_irrigation_system.logger import get_dashboard_log_handler
from smart_irrigation_system.__version__ import __version__ as version
from smart_irrigation_system.enums import ControllerState

class IrrigationCLI:
    def __init__(self, controller: IrrigationController, refresh_interval_idle=1, refresh_interval_active=0.1,
                max_logs=20, sleep_timeout=30):
        self.controller = controller
        self.refresh_interval_idle = refresh_interval_idle
        self.refresh_interval_active = refresh_interval_active
        self.running = True
        self.console = Console()
        self.logs = []  # own log storage
        self.max_logs = max_logs
        self.input_cmd = ""  # stores the current input command
        self.live = None

        # Sleep mode
        self.last_activity = time.time()
        self.sleep_timeout = sleep_timeout  # seconds before going to sleep
        self.sleeping = False

        # Help
        self.showing_help = False

        self.log_handler = get_dashboard_log_handler(max_logs=max_logs)
        logging.getLogger().addHandler(self.log_handler)

        self.input_thread = threading.Thread(target=self.input_loop, daemon=True)
        self.input_thread_stop = threading.Event()  # Event to stop the input thread

    def add_log(self, message: str):
        timestamp = time.strftime("%H:%M:%S")
        self.logs.append(f"[{timestamp}] {message}")
        if len(self.logs) > self.max_logs:
            self.logs.pop(0)



    def run(self):
        # Start the input thread
        self.input_thread.start()

        # Start the sleep watcher thread
        sleep_thread = threading.Thread(target=self.sleep_watcher, daemon=True)
        sleep_thread.start()

        with Live(auto_refresh=False, console=self.console, screen=True) as live:
            self.live = live
            while self.running:
                if self.showing_help:
                    # If help is being shown, render the help dashboard
                    dashboard = self.render_help()
                else:
                    # Render the main dashboard
                    dashboard = self.render_dashboard()

                # Adaptive refresh interval based on controller state
                if self.controller.get_state() == ControllerState.IRRIGATING:
                    refresh_interval = self.refresh_interval_active
                else:
                    refresh_interval = self.refresh_interval_idle

                live.update(dashboard, refresh=True)
                time.sleep(refresh_interval)

    # ===========================================================================================================
    # Sleep mode methods
    # ===========================================================================================================

    def enter_sleep_mode(self):
        """Enter sleep mode if there is no activity for a specified timeout."""
        self.sleeping = True
        if self.live:
            self.live.stop()
        self.console.clear()
        sleep_msg = Align.center(Text("💤 CLI in sleep mode due to inactivity.\n\nPress 'Enter' to wake up.", justify="center", style="dim"), vertical="middle")
        sleep_panel = Align.center(
        Panel(sleep_msg,
              border_style="yellow", title="Sleep Mode", padding=(1, 2)),
        vertical="middle"
    )
        self.console.print(sleep_panel)

        while self.sleeping and self.running:
            time.sleep(0.1)

        if self.live:
            self.live.start()

    def sleep_watcher(self):
        """Monitor for inactivity and put the CLI to sleep if needed."""
        while self.running:
            current_time = time.time()
            if current_time - self.last_activity > self.sleep_timeout and not self.sleeping:
                self.enter_sleep_mode()
            time.sleep(1)


    # ===========================================================================================================
    # Input handling methods
    # ===========================================================================================================

    def input_loop(self):
        while self.running:
            try:
                cmd = input("> ").strip()
                if self.sleeping:
                    self.sleeping = False  # Wake up if input is received
                    self.last_activity = time.time()
                    continue
                elif self.showing_help:
                    self.showing_help = False
                    self.last_activity = time.time()
                    continue

                self.last_activity = time.time()  # Update last activity time
                self.input_cmd = cmd
                self.handle_command(cmd)
                self.input_cmd = ""  # clear prompt after handling command
            except EOFError:
                break
            except KeyboardInterrupt:
                self.running = False
                break

    def handle_command(self, cmd: str):
        """Handle user commands."""
        cmd = cmd.lower()
        if cmd == "irrigate":
            self.controller.start_automatic_irrigation()
            self.add_log("Start automatic irrigation.")
        elif cmd == "stop":
            self.controller.stop_irrigation()
            self.add_log("Stop irrigation.")
        elif cmd == "auto on":
            self.controller.start_main_loop()
            self.add_log("Enable automatic loop.")
        elif cmd == "auto off":
            self.controller.stop_main_loop()
            self.add_log("Disable automatic loop.")
        elif cmd == "auto pause":
            self.controller.pause_main_loop()
            self.add_log("Pause automatic loop.")
        elif cmd == "auto resume":
            self.controller.resume_main_loop()
            self.add_log("Resume automatic loop.")
        elif cmd in ("quit", "shutdown", "exit"):
            self.add_log("Shutdown system.")
            self.cleanup()
        elif cmd == "help":
            self.showing_help = True
            self.render_help()
        else:
            self.add_log(f"Unknown command: {cmd}")

    # ===========================================================================================================
    # Rendering methods
    # ===========================================================================================================

    def render_help(self):
        """ Render help information for the CLI commands."""
        commands = [
                "irrigate - Start automatic irrigation",
                "stop - Stop all irrigation",
                "auto on - Enable automatic mode",
                "auto off - Disable automatic mode",
                "auto pause - Pause automatic mode",
                "auto resume - Resume automatic mode",
                "quit/exit/shutdown - Exit the dashboard and shutdown system",
                "help - Show help information",
            ]
        help_dashboard = Table.grid(expand=True)
        commands_text = Text("\n".join(commands), style="green")
        commands_panel = Panel(commands_text, title="Available Commands", expand=True)
        return_text = Text("Press 'Enter' to return to dashboard.", style="yellow")
        help_dashboard.add_row(commands_panel)
        help_dashboard.add_row(Align.center(return_text, vertical="middle"))

        return help_dashboard

    def render_dashboard(self):
        status = self.controller.get_status()

        state_icons = {
            "IDLE": "⚪",
            "IRRIGATING": "💧",
            "WAITING": "⏳",
            "STOPPING": "⏹️",
            "ERROR": "❌"
        }

        # 1) System status
        sys_table = Table.grid(expand=True)
        sys_table.add_column(justify="left")
        sys_table.add_column(justify="left")
        sys_table.add_row("Mode", f"{'AUTO' if status['auto_enabled'] else 'MANUAL'} "
                                  f"{'(OFF)' if status['auto_stopped'] else '(ON)'}"
                                  f"{' - paused' if status['auto_paused'] else ''}", f"version {version}")
        sys_table.add_row("Irrigation mode", f"{'Sequential' if status['sequential'] else 'Concurrent'} ")
        
        # add current time
        current_time = datetime.datetime.now().strftime("%H:%M:%S")
        sys_table.add_row("Current time", current_time)
        sys_table.add_row("Scheduled time", f"{status['scheduled_time']}" if status['auto_enabled'] else "N/A")
        # add empty row for spacing
        sys_table.add_row("", "")
        sys_table.add_row("Cached weather", status['cached_global_conditions'])
        sys_table.add_row("Last weather update", str(status['cache_update']))
        # add empty row for spacing
        sys_table.add_row("", "")
        current_consumption = status['current_consumption']
        if current_consumption > 1000:
            cc_str = Text(f"{current_consumption:.2f} L/h", style="#eb8934")
        elif current_consumption > 500:
            cc_str = Text(f"{current_consumption:.2f} L/h", style="yellow")
        elif current_consumption > 0:
            cc_str = Text(f"{current_consumption:.2f} L/h", style="green")
        else:
            cc_str = Text("0.00 L/h", style="dim")
        sys_table.add_row("Current consumption", cc_str)
        sys_table.add_row("Controller state", f"{state_icons.get(status['controller_state'], '?')} {status['controller_state']}")

        # 2) Zones
        zones_table = Table(title="Zones", expand=True)
        zones_table.add_column("ID", justify="center")
        zones_table.add_column("Name")
        zones_table.add_column("Last irrigation time")
        zones_table.add_column("Last volume")
        zones_table.add_column("Base volume")
        zones_table.add_column("Last result")
        zones_table.add_column("State", justify="center")
        zones_table.add_column("Pin", justify="center")


        for z in status['zones']:
            icon = state_icons.get(z['state'], "?")
            base_volume: float = self.controller.get_circuit(z['id']).base_target_water_amount
            bv_str = f"{base_volume:.2f} L" if base_volume is not None else "N/A"
            time: Optional[datetime] = self.controller.get_circuit(z['id']).last_irrigation_time
            if time is None:
                t_str: Text = Text("N/A", style="dim")
            # if the date is today, show only time
            elif time.date() == datetime.datetime.now().date():
                t_str: Text = Text(time.strftime("Today %H:%M:%S"))
            else:
                # if the date is not today, show full date and time in dim style
                t_str: Text = Text(time.strftime("%d.%m.%Y %H:%M:%S"), style="dim")

            vol = self.controller.get_circuit(z['id']).last_irrigation_volume
            if vol is None:
                v_str: Text = Text("N/A", style="dim")
            elif vol > base_volume:
                v_str: Text = Text(f"{vol:.2f} L", style="#eb8934")
            else:
                v_str: Text = Text(f"{vol:.2f} L", style="green")
            
            result = self.controller.get_circuit(z['id'])._last_irrigation_result
            if result is None:
                r_str = Text("N/A", style="dim")
            elif result == "success":
                r_str = Text("Success", style="green")
            elif result == "skipped":
                r_str = Text("Skipped")
            elif result == "interrupted":
                r_str = Text("Interrupted", style="yellow")
            elif result == "error":
                r_str = Text("Error", style="red")

            zones_table.add_row(str(z['id']), z['name'], t_str, v_str, bv_str, r_str,
                                f"{icon} {z['state']}", str(z['pin']))

        # 3) Current tasks panel - live progress bar of irrigating zones
        irrigating_zones = {z['name']: z['id'] for z in status['zones'] if z['state'] == 'IRRIGATING'}

        tasks_panel_content = []
        for name, zone_id in irrigating_zones.items():
            target_water_amount, current_water_amount = self.controller.get_circuit_progress(zone_id)
            
            # Format zone ID (max 3 characters)
            zone_id_str = str(zone_id)[:2]

            # Format zone name (max 25 characters)
            zone_name = name[:25] + ("..." if len(name) > 25 else "")
            
            # Format water amount (max 20 characters)
            water_amount = f"{current_water_amount:.2f} / {target_water_amount:.2f} L"
            
            # Create live progress bar (remaining width, at least 50 characters)
            if target_water_amount > 0:
                progress_percentage = int((current_water_amount / target_water_amount) * 75)
                progress_bar = f"[{'█' * progress_percentage}{'-' * (75 - progress_percentage)}]"
            else:
                progress_bar = "[---------------------------------------------------------------]"
            
            # Add formatted row to content
            tasks_panel_content.append(
                f"{zone_id_str:<2} {zone_name:<25} {water_amount:<20} {progress_bar:>75}"
            )

            # Add a separator line for minimal spacing
            tasks_panel_content.append(" " * 3)  # Add 3 spaces for padding

        # Combine all rows into a single string
        tasks_panel_text = "\n".join(tasks_panel_content) or "No tasks currently running."

        # Create the panel
        tasks_panel = Panel(
            tasks_panel_text,
            title="Current Tasks",
            expand=True,
            border_style="bold yellow"
        )


        # 4) Command logs panel
        # Create a text representation of the 3 recent logs
        logs_text = "\n".join(self.logs[-3:]) if self.logs else ""
        cmd_logs_panel = Panel(logs_text or "No logs yet.", title="Command Logs", expand=True)
        

        # 5) System log panel
        logs_rich = []
        level_styles = {
            "INFO": "green",
            "WARNING": "#eb8934",
            "ERROR": "red",
            "CRITICAL": "bold white on red",
            "DEBUG": "cyan",
        }

        for level, raw in self.log_handler.logs:
            try:
                parts = [p.strip() for p in raw.split("|", 3)]
                if len(parts) == 4:
                    timestamp, module, lvl, message = parts
                else:
                    timestamp, module, lvl, message = "?", "?", level, raw

                style = level_styles.get(level, "white")

                line = Text(f"[{level}] ", style=style)
                line.append(f"{timestamp[11:]} | {module} | {message[:80]}", style="dim white")

                logs_rich.append(line)
            except Exception as e:
                logs_rich.append(Text(f"Parse error: {raw}", style="red"))

        logs_panel = Panel(
            Align.left(Text("\n").join(logs_rich)) if logs_rich else "No logs yet.",
            title="Recent Logs",
            expand=True
        )

        # 6) Help text
        help_text = Text("Type 'help' for available commands.", style="yellow")


        # 7) Assemble the dashboard
        dashboard = Table.grid(expand=True)
        dashboard.add_row(Panel(sys_table, title="System Status", expand=True))
        dashboard.add_row(zones_table)
        if irrigating_zones:
            dashboard.add_row(tasks_panel)
        dashboard.add_row(logs_panel)
        dashboard.add_row(cmd_logs_panel)
        dashboard.add_row(Align.center(help_text, vertical="middle"))  # Centered help text
        return dashboard


    # ===========================================================================================================
    # Cleanup and shutdown
    # ===========================================================================================================

    def cleanup(self):
        """Cleanup resources."""
        self.running = False
        self.input_thread_stop.set()  # Signal the input thread to stop
        if self.live:
            self.live.stop()
        logging.getLogger().removeHandler(self.log_handler)
        self.console.clear()
    
