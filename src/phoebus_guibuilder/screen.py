import phoebusgen.screen as Screen
import phoebusgen.widget as Widget

from phoebus_guibuilder.datatypes import Entry


class TechUIScreens:
    def __init__(self, screen_components: list[Entry], screen: dict):
        self.screen_components = screen_components
        self.screen_ = Screen.Screen(self.screen_components[0].DESC)
        widgets = []

        self.P: str = "P"
        self.M: str = "M"

        for order, ui in enumerate(self.screen_components):
            if ui.M is not None:
                name = ui.M
            else:
                name = ui.type

            widgets.append(
                Widget.EmbeddedDisplay(
                    name,
                    "./techui-support/bob/" + screen[ui.type]["file"],
                    (10 + 2 * order),
                    (10 + 2 * order),
                    700,
                    700,
                )
            )
            widgets[order].macro(self.P, ui.P)
            widgets[order].macro(self.M, ui.M)

            self.screen_.add_widget(widgets[order])

        self.screen_.write_screen(self.screen_components[0].DESC + ".bob")
