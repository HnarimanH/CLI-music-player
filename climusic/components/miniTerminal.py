from textual.widgets import Input, Static, RichLog
from textual.containers import Vertical
from textual.app import ComposeResult
import pyperclip


class MiniTerminal(Vertical):

    def compose(self) -> ComposeResult:
        yield Static("terminal", id="terminal-header")
        yield RichLog(id="terminal-log", markup=True, highlight=True)
        yield Input(placeholder="enter command...", id="terminal-input")

    def on_mount(self) -> None:
        self.history = []
        self.history_index = -1
        self.write("[dim]ready. type a command below.[/dim]")
        self.write("[dim][/dim]")
        
        input_widget = self.query_one("#terminal-input", Input)
        input_widget.focus()

    def write(self, msg: str) -> None:
        log = self.query_one("#terminal-log", RichLog)
        log.write(msg)
        log.scroll_end(animate=False)

    def on_input_submitted(self, event: Input.Submitted) -> None:
        cmd = event.value.strip()
        if not cmd:
            return

        if not self.history or self.history[0] != cmd:
            self.history.insert(0, cmd)
        self.history_index = -1

        event.input.value = ""
        self.write(f"[dim]>[/dim] {cmd}")
        self.app.handle_command(cmd)
        
        # Refocus after command
        self.query_one("#terminal-input", Input).focus()

    def _on_key(self, event) -> None:
        """Handle Ctrl+V for paste"""
        input_widget = self.query_one("#terminal-input", Input)
        
        if event.key == "ctrl+v":
            try:
                clipboard = pyperclip.paste()
                input_widget.value = clipboard
                input_widget.cursor_position = len(clipboard)
            except Exception as e:
                self.write(f"[red]paste error: {e}[/red]")
            event.prevent_default()