from rich.live import Live
from rich.table import Table
from rich.console import Console
from rich.panel import Panel
from rich.align import Align
from rich.text import Text
import threading
import time, logging

from smart_irrigation_system.irrigation_controller import IrrigationController
from smart_irrigation_system.logger import DashboardLogHandler

class IrrigationCLI:
    def __init__(self, controller: IrrigationController, refresh_interval=1.0, max_logs=20):
        self.controller = controller
        self.refresh_interval = refresh_interval
        self.running = True
        self.console = Console()
        self.logs = []  # own log storage
        self.max_logs = max_logs
        self.input_cmd = ""  # stores the current input command
        self.live = None

        self.log_handler = DashboardLogHandler(max_logs=5)
        logging.getLogger().addHandler(self.log_handler)

    def add_log(self, message: str):
        timestamp = time.strftime("%H:%M:%S")
        self.logs.append(f"[{timestamp}] {message}")
        if len(self.logs) > self.max_logs:
            self.logs.pop(0)

    def render_help(self):
        commands = [
            "irrigate - Start automatic irrigation",
            "stop - Stop all irrigation",
            "auto on - Enable automatic mode",
            "auto off - Disable automatic mode",
            "auto pause - Pause automatic mode",
            "auto resume - Resume automatic mode",
            "quit/exit - Exit the dashboard",
            "help - Show help information",
        ]
        # Format as rich text (green) with line breaks
        commands_text = Text("\n".join(commands), style="green")
        commands_panel = Panel(commands_text, title="Available Commands", expand=True)
        commands_panel.title_align = "center"
        commands_panel.title_style = "bold"
        commands_panel.border_title = "Commands"

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
                                  f"{' - paused' if status['auto_paused'] else ''}")
        sys_table.add_row("Irrigation Mode", f"{'Sequential' if status['sequential'] else 'Concurrent'} ")
        
        # add current time
        sys_table.add_row("Current time", time.strftime("%H:%M:%S"))
        sys_table.add_row("Scheduled time", f"{status['scheduled_time']}" if status['auto_enabled'] else "N/A")
        # add empty row for spacing
        sys_table.add_row("", "")
        sys_table.add_row("Cached Weather", status['cached_global_conditions'])
        sys_table.add_row("Last Weather Update", str(status['cache_update']))
        # add empty row for spacing
        sys_table.add_row("", "")
        sys_table.add_row("Consumption", f"{status['current_consumption']:.2f} L/h")
        sys_table.add_row("Controller State", f"{state_icons.get(status['controller_state'], '?')} {status['controller_state']}")

        # 2) Zones
        zones_table = Table(title="Zones", expand=True)
        zones_table.add_column("ID", justify="center")
        zones_table.add_column("Name")
        zones_table.add_column("Last Irrigation")
        zones_table.add_column("State", justify="center")
        zones_table.add_column("Pin", justify="center")


        for z in status['zones']:
            icon = state_icons.get(z['state'], "?")
            i_t = self.controller.get_circuit(z['id']).last_irrigation_time
            zones_table.add_row(str(z['id']), z['name'], i_t.strftime("%H:%M:%S") if i_t else "N/A",
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
        

        # 5) system log panel
        logs_text = "\n".join(f"[{level}] {msg}" for level, msg in self.log_handler.logs)
        logs_panel = Panel(logs_text or "No logs yet.", title="Recent Logs", expand=True)

        help_text = Text("Type 'help' for available commands.", style="yellow")


        # 6) Assemble the dashboard
        dashboard = Table.grid(expand=True)
        dashboard.add_row(Panel(sys_table, title="System Status", expand=True))
        dashboard.add_row(zones_table)
        if irrigating_zones:
            dashboard.add_row(tasks_panel)
        dashboard.add_row(logs_panel)
        dashboard.add_row(cmd_logs_panel)
        dashboard.add_row(Align.center(help_text, vertical="middle"))  # Centered help text
        return dashboard

    def input_loop(self):
        while self.running:
            try:
                cmd = input("> ").strip()
                self.input_cmd = cmd
                self.handle_command(cmd)
                self.input_cmd = ""  # vymaže prompt po zadání
            except EOFError:
                break
            except KeyboardInterrupt:
                self.running = False
                break

    def handle_command(self, cmd: str):
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
        elif cmd in ("quit", "exit"):
            self.running = False
            self.add_log("Exit dashboard.")
        elif cmd == "help":
            # --- HELP LOGIC ---
            
            commands = [
                "irrigate - Start automatic irrigation",
                "stop - Stop all irrigation",
                "auto on - Enable automatic mode",
                "auto off - Disable automatic mode",
                "auto pause - Pause automatic mode",
                "auto resume - Resume automatic mode",
                "quit/exit - Exit the dashboard",
                "help - Show help information",
            ]
            commands_text = Text("\n".join(commands), style="green")
            commands_panel = Panel(commands_text, title="Available Commands", expand=True)
            self.live.stop()
            self.console.clear()
            self.console.print(commands_panel)
            input("\nPress Enter to return to dashboard...")
            self.live.start()
        else:
            self.add_log(f"Unknown command: {cmd}")

    def run(self):
        input_thread = threading.Thread(target=self.input_loop, daemon=True)
        input_thread.start()

        with Live(auto_refresh=False, console=self.console, screen=True) as live:
            self.live = live
            while self.running:
                dashboard = self.render_dashboard()
                live.update(dashboard, refresh=True)
                time.sleep(self.refresh_interval)
