from ..ui.buttons import InputBox, TitleOfInputBox


class UserInput:
    def __init__(
        self,
        screen,
        fields: dict[str, str],
        x: float,
        y: float,
        y_step: float,
        default_values: dict[str, str] | None = None,
    ):
        self.screen = screen
        self.fields = fields
        self.input_boxes = {}
        self.title_boxes = {}
        if default_values is None:
            default_values = {}
        for field, label in fields.items():
            self.title_boxes[field] = TitleOfInputBox(screen, title_text=label, x=x, y=y)
            self.input_boxes[field] = InputBox(
                screen,
                type_text=field,
                x=x,
                y=y + y_step,
                initial_text=default_values.get(field, ""),
            )
            y += y_step * 4

    def handle_event(self, event):
        for box in self.input_boxes.values():
            box.handle_event(event)

    def draw(self):
        for box in self.input_boxes.values():
            box.draw(self.screen)
        for title in self.title_boxes.values():
            title.draw(self.screen)

    def get_values(self) -> dict[str, str]:
        return {field: box.text for field, box in self.input_boxes.items()}
