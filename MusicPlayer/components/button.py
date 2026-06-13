from textual.widgets import Button
from textual.reactive import reactive


class FlexibleButton(Button):
    """A flexible toggle button widget with icons for on and off states."""
    
    is_on = reactive(False)
    
    def __init__(
        self,
        label: str = "",
        *,
        size: str = "auto",
        icon_on: str = "",
        icon_off: str = "",
        on_click_function=None,
        **kwargs
    ):
        """
        Initialize a toggle button.
        
        Args:
            label: Button text label
            size: Button size (e.g., "auto", "1fr", "20")
            icon_on: Icon to display when button is on
            icon_off: Icon to display when button is off
            on_click_function: Callable function to execute on click
            **kwargs: Additional arguments to pass to Button
        """
        self.size = size
        self.icon_on = icon_on
        self.icon_off = icon_off
        self.on_click_function = on_click_function
        self.label = label
        
        button_label = f"{icon_off} {label}".strip() if icon_off else label
        super().__init__(button_label, **kwargs)
    
    def render(self) -> str:
        """Render button with appropriate icon based on state."""
        icon = self.icon_on if self.is_on else self.icon_off
        return f"{icon} {self.label}".strip() if icon else self.label
    
    async def _on_press(self) -> None:
        """Handle button press event and toggle state."""
        self.is_on = not self.is_on
        if self.on_click_function:
            result = self.on_click_function(self.is_on)
            if hasattr(result, '__await__'):
                await result
        await super()._on_press()
