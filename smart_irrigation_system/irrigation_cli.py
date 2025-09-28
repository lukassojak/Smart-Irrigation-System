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
from smart_irrigation_system.logger import get_logger

class IrrigationCLI:
    def __init__(self, controller: IrrigationController, refresh_interval_idle=1, refresh_interval_active=0.1,
                max_logs=20, sleep_timeout=300):
        self.controller = controller
        self.refresh_interval_idle = refresh_interval_idle
        self.refresh_interval_active = refresh_interval_active
        self.running = True
        self.console = Console()
        self.logs = []  # own log storage
        self.max_logs = max_logs
        self.input_cmd = ""  # stores the current input command
        self.live = None
        self.logger = get_logger("IrrigationCLI")

        # Sleep mode
        self.last_activity = time.time()
        self.sleep_timeout = sleep_timeout  # seconds before going to sleep
        self.sleeping = False

        # Help
        self.showing_help = False

        # History of irrigation
        self.showing_history = False

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
                    try:
                        dashboard = self.render_help()
                    except Exception as e:
                        self.logger.error(f"Error rendering help: {e}")
                        dashboard = Panel(Text("Error rendering help.", style="red"), title="Help - Error", expand=True)
                        time.sleep(10) # wait before retrying
                else:
                    # Render the main dashboard
                    try:
                        dashboard = self.render_dashboard()
                    except Exception as e:
                        self.logger.error(f"Error rendering dashboard: {e}")
                        dashboard = Panel(Text("Error rendering dashboard.", style="red"), title="Dashboard - Error", expand=True)
                        time.sleep(10)

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
                elif self.showing_history:
                    self.showing_history = False
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
            self.add_log("'irrigate': Start automatic irrigation now.")
            self.controller.start_automatic_irrigation()
        elif cmd.startswith("irrigate "):
            parts = cmd.split()
            if len(parts) == 3 and parts[1].isdigit():
                zone_id = int(parts[1])
                try:
                    volume = float(parts[2])
                    if volume <= 0:
                        self.add_log(f"Volume must be positive. Given: {volume}")
                        return
                    try:
                        self.controller.get_circuit(zone_id)
                    except ValueError:
                        self.add_log(f"Zone ID {zone_id} does not exist.")
                        return
                    self.add_log(f"'irrigate {zone_id} {volume}': Start irrigation of zone {zone_id} with {volume} liters.")
                    self.controller.manual_irrigation(zone_id, volume)
                except ValueError:
                    self.add_log(f"Invalid volume: {parts[2]}. Must be a number.")
                except RuntimeError as e:
                    self.add_log(f"Cannot start irrigation: {e}")
            else:
                self.add_log("Invalid command format. Use 'irrigate <zone_id> <volume_liters>'.")
        elif cmd == "stop":
            self.add_log("'Stop': Stop all irrigation.")
            self.controller.stop_irrigation()
        elif cmd == "auto on":
            self.add_log("'auto on': Enable auto mode.")
            self.controller.start_main_loop()
        elif cmd == "auto off":
            self.add_log("'auto off': Disable auto mode.")
            self.controller.stop_main_loop()
        elif cmd == "auto pause":
            self.add_log("'auto pause': Pause auto mode. Next scheduled irrigation will be skipped.")
            self.controller.pause_main_loop()
        elif cmd == "auto resume":
            self.add_log("'auto resume': Resume auto mode. Next scheduled irrigation will be executed.")
            self.controller.resume_main_loop()
        elif cmd == "shutdown":
            self.add_log("Shutdown system now.")
            self.cleanup()
        elif cmd == "update weather":
            self.add_log("'update weather': Update cached weather conditions.")
            self.controller.global_conditions_provider.get_current_conditions(force_update=True)
        elif cmd == "history":
            self.add_log("'history': Show irrigation history.")
            self.showing_history = True
            history_panel = self.render_history()
            self.console.print(history_panel)
            self.console.input("Press 'Enter' to return to dashboard.")
            self.showing_history = False
        elif cmd == "help":
            self.add_log("'help': Show help information.")
            self.showing_help = True
            self.render_help()
        else:
            self.add_log(f"{cmd}: Unknown command. Type 'help' for available commands.")

    # ===========================================================================================================
    # Rendering methods
    # ===========================================================================================================

    def render_help(self):
        """ Render help information for the CLI commands."""
        commands = [
                "irrigate - Start automatic irrigation now",
                "irrigate <zone_id> <volume_liters> - Irrigate specific zone with specified volume (e.g., 'irrigate 1 10')",
                "stop - Stop all irrigation",
                "auto on - Enable automatic mode",
                "auto off - Disable automatic mode",
                "auto pause - Pause automatic mode (Next scheduled irrigation will be skipped)",
                "auto resume - Resume automatic mode (Next scheduled irrigation will be executed)",
                "quit/exit/shutdown - Exit the dashboard and shutdown system",
                "update weather - Update cached weather conditions",
                "help - Show help information",
            ]
        help_dashboard = Table.grid(expand=True)
        help_dashboard.add_column(justify="left")
        help_dashboard.add_column(justify="left")
        irrigate = Text("irrigate", style="bold green")
        irrigate_doc = Text("Start automatic irrigation now", style="dim")
        irrigate_manual = Text("irrigate <zone_id> <volume_liters>", style="bold green")
        irrigate_manual_doc = Text("Irrigate specific zone with specified volume in liters (e.g., 'irrigate 1 10')", style="dim")
        stop = Text("stop", style="bold green")
        stop_doc = Text("Stop all irrigation", style="dim")
        auto_on = Text("auto on", style="bold green")
        auto_on_doc = Text("Enable automatic mode", style="dim")
        auto_off = Text("auto off", style="bold green")
        auto_off_doc = Text("Disable automatic mode", style="dim")
        auto_pause = Text("auto pause", style="bold green")
        auto_pause_doc = Text("Pause automatic mode (Next scheduled irrigation will be skipped)", style="dim")
        auto_resume = Text("auto resume", style="bold green")
        auto_resume_doc = Text("Resume automatic mode (Next scheduled irrigation will be executed)", style="dim")
        shutdown = Text("shutdown", style="bold green")
        shutdown_doc = Text("Exit the dashboard and shutdown system", style="dim")
        update_weather = Text("update weather", style="bold green")
        update_weather_doc = Text("Update cached weather conditions", style="dim")
        help = Text("help", style="bold green")
        help_doc = Text("Show help information", style="dim")

        # assemble the commands in a panel
        help_dashboard.add_row(irrigate, irrigate_doc)
        help_dashboard.add_row(irrigate_manual, irrigate_manual_doc)
        help_dashboard.add_row(stop, stop_doc)
        help_dashboard.add_row(auto_on, auto_on_doc)
        help_dashboard.add_row(auto_off, auto_off_doc)
        help_dashboard.add_row(auto_pause, auto_pause_doc)
        help_dashboard.add_row(auto_resume, auto_resume_doc)
        help_dashboard.add_row(shutdown, shutdown_doc)
        help_dashboard.add_row(update_weather, update_weather_doc)
        help_dashboard.add_row(help, help_doc)

        # Add return information
        return_text = Text("Press 'Enter' to return to dashboard.", style="yellow")
        help_dashboard.add_row("", return_text)

        help_dashboard = Panel(help_dashboard, title="Help - Available Commands", expand=True, border_style="white")

        return help_dashboard

    def render_dashboard(self):
        status = self.controller.get_status()

        state_icons = {
            "IDLE": "⚪",
            "IRRIGATING": "💧",
            "WAITING": "⏳",
            "STOPPING": "⏹️",
            "ERROR": "❌",
            "DISABLED": "🚫",
        }

        weather_cache_state_icons = {
            "connecting": "🔄",
            "disconnected": "🟡",
            "fetched": "🟢",
            "disabled": "🚫",
            "invalid_secrets": "❌",
            "error": "🔴",
        }

        # 1) System status
        sys_table = Table.grid(expand=True)
        sys_table.add_column(justify="left")
        sys_table.add_column(justify="left")
        sys_table.add_column(justify="left")
        sys_table.add_row("Mode", f"{'AUTO' if status['auto_enabled'] else 'MANUAL'} "
                                  f"{'(OFF)' if status['auto_stopped'] else '(ON)'}"
                                  f"{' - paused' if status['auto_paused'] else ''}", "", f"version {version}")
        sys_table.add_row("Irrigation mode", f"{'Sequential' if status['sequential'] else 'Concurrent'} ")
        
        # add current time
        current_time = datetime.datetime.now().strftime("%H:%M:%S")
        sys_table.add_row("Current time", current_time)
        sys_table.add_row("Scheduled time", f"{status['scheduled_time']}" if status['auto_enabled'] else "N/A")
        # add empty row for spacing
        sys_table.add_row("", "")
        wd_s = Text("")
        cache_interval_days = Text("")
        if self.controller.global_conditions_provider.connecting:
            w_s = weather_cache_state_icons['connecting'] + " Connecting..."
            if self.controller.global_conditions_provider.last_cache_update != datetime.datetime.min:
                cache_interval_days = Text(f"(from the last {self.controller.global_conditions_provider.max_interval_days} days)", style="dim")
        elif not self.controller.global_config.weather_api.api_enabled:
            w_s = weather_cache_state_icons['disabled'] + " Disabled (using standard conditions)"
        elif self.controller.global_conditions_provider.last_cache_update == datetime.datetime.min:
            w_s = weather_cache_state_icons['error'] + " No data"
        elif self.controller.global_conditions_provider.try_reconnect:
            w_s = weather_cache_state_icons['disconnected'] + " Disconnected"
            cache_interval_days = Text(f"(from the last {self.controller.global_conditions_provider.max_interval_days} days)", style="dim")
        elif self.controller.global_conditions_provider._use_standard_conditions:
            w_s = weather_cache_state_icons['invalid_secrets'] + " Invalid API settings"
        elif self.controller.global_conditions_provider.current_conditions is None:
            w_s = weather_cache_state_icons['error'] + " No data"
        elif self.controller.global_conditions_provider.current_conditions is not None:
            api_url = self.controller.global_config.weather_api.realtime_url[:self.controller.global_config.weather_api.realtime_url.find(".net")+4] if self.controller.global_config.weather_api.realtime_url else "N/A"
            w_s = weather_cache_state_icons['fetched'] + " Connected"
            wd_s = Text(api_url, style="dim")
            cache_interval_days = Text(f"(from the last {self.controller.global_conditions_provider.max_interval_days} days)", style="dim")
        else:
            w_s = weather_cache_state_icons['error'] + " Error"

        sys_table.add_row("Weather status", w_s, wd_s)
        sys_table.add_row("Cached weather", f"{status['cached_global_conditions']}" if status['cached_global_conditions'] else "N/A", cache_interval_days)
        sys_table.add_row("Weather cache update", str(status['cache_update'].strftime("%d.%m.%Y %H:%M:%S")) if status['cache_update'] else "N/A")

        # add empty row for spacing
        sys_table.add_row("", "")
        current_consumption = status['current_consumption']
        current_consumption_color = self.get_consumption_color(current_consumption, status['input_flow_capacity'])
        cc_str = Text(f"{current_consumption:.2f} L/h", style=current_consumption_color)
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
        zones_table.add_column("State")
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
            elif vol == 0:
                v_str: Text = Text(f"{vol:.2f} L", style="dim")
            elif vol > base_volume:
                v_str: Text = Text(f"{vol:.2f} L", style="orange3")
            else:
                v_str: Text = Text(f"{vol:.2f} L", style="green")
            
            result = self.controller.get_circuit(z['id'])._last_irrigation_result
            if result is None:
                r_str = Text("N/A", style="dim")
            elif result == "success":
                r_str = Text("Success", style="green")
            elif result == "skipped":
                r_str = Text("Skipped", style="green")
            elif result == "interrupted":
                r_str = Text("Interrupted", style="yellow")
            elif result == "error":
                r_str = Text("Error", style="red")
            elif result == "failed":
                r_str = Text("Failed", style="orange3")
            elif result == "stopped":
                r_str = Text("Stopped", style="yellow")
            else:
                r_str = Text(result)

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

            # Simulate CLI crash during irrigation for testing purposes
            if current_water_amount > target_water_amount / 4:
                self.add_log("Simulated crash for testing purposes.")
                raise Exception("Simulated crash for testing purposes.")

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
            "WARNING": "orange3",
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
                if level == "CRITICAL":
                    line.append(f"{timestamp[11:]} | {module} | {message[:80]}", style="bold white on red")
                else:
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
    
    def render_history(self):
        """Render the irrigation history table."""
        history_table = Table(title="Irrigation History", expand=True)
        history_table.add_column("Date")
        history_table.add_column("Weather")
        history_table.add_column("Zone 1")
        history_table.add_column("Zone 2")
        history_table.add_column("Zone 3")

        return Panel(history_table, title="Irrigation History", expand=True)

    def get_consumption_color(self, consumption: float, capacity: float) -> str:
        """Get color based on consumption percentage."""
        if consumption <= 0:
            return "dim"
        elif capacity <= 0:
            return "red"
        percentage = (consumption / capacity) * 100
        if percentage < 50:
            return "green"
        elif percentage < 80:
            return "yellow"
        elif percentage < 100:
            return "orange3"
        else:
            return "red"



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
    
