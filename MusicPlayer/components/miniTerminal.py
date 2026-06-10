from textual.widgets import Input, Static, RichLog
from textual.containers import Vertical
from textual.app import ComposeResult


class MiniTerminal(Vertical):
   

    def compose(self) -> ComposeResult:
        yield Static("terminal", id="terminal-header")
        yield RichLog(id="terminal-log", markup=True, highlight=True)
        yield Input(placeholder="enter command...", id="terminal-input")

    def on_mount(self) -> None:
        self.write("[dim]ready. type a command below.[/dim]")
        self.write("[dim][/dim]")

    def write(self, msg: str) -> None:
        log = self.query_one("#terminal-log", RichLog)
        log.write(msg)
        log.scroll_end(animate=False)

    def on_input_submitted(self, event: Input.Submitted) -> None:
        cmd = event.value.strip()
        if not cmd:
            return

        event.input.value = ""
        self.write(f"[dim]>[/dim] {cmd}")
        self.app.handle_command(cmd)