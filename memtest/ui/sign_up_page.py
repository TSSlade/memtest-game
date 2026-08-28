import json
from pathlib import Path

import pygame

from ..config.session_config import SessionConfig
from ..config.signup_config import SignUpConfig
from ..paths import CONFIG_DIR
from ..user.user_info import UserInfo
from ..user.user_input import UserInput
from .buttons import NextButton, Title


class SignUp:
    def __init__(
        self,
        screen,
        screen_color,
        config: SignUpConfig | None = None,
        config_path: Path | None = None,
    ):
        self.screen = screen
        self.screen_color = screen_color
        screen_width, screen_height = self.screen.get_size()
        self.title_box = Title(self.screen, show_up_text="Sign Up")
        self.next_button = NextButton(self.screen)
        blank_spc = screen_height // 27
        if config is None:
            config = SignUpConfig()
        x_init_1 = 1 * screen_width / 5
        y_init_1 = screen_height / 4
        x_init_2 = 3 * screen_width / 5
        y_init_2 = screen_height / 4
        self.user_input = UserInput(
            self.screen, config.user_fields, x_init_1, y_init_1, blank_spc
        )
        # Load session defaults from config file
        session_defaults = self._load_session_defaults(config_path)
        self.session_input = UserInput(
            self.screen,
            config.session_fields,
            x_init_2,
            y_init_2,
            blank_spc,
            default_values=session_defaults,
        )

    def _load_session_defaults(self, config_path: Path | None = None) -> dict[str, str]:
        """Load session defaults from JSON config file.

        If config_path is provided and exists, load from it.
        Otherwise, use SessionConfig defaults.
        """
        if config_path is None:
            config_path = CONFIG_DIR / "config.json"

        if config_path.exists():
            try:
                with open(config_path, encoding="utf-8") as f:
                    config_data = json.load(f)
                session_data = config_data.get("session", {})
                if session_data:
                    print(f"[INFO] Using configuration from {config_path}")
                    # Convert all values to strings for input boxes
                    return {k: str(v) for k, v in session_data.items()}
            except (OSError, json.JSONDecodeError) as e:
                print(f"[WARNING] Failed to load config from {config_path}: {e}")
        else:
            print(
                "[INFO] Using default configuration (no config.json found). "
                "Copy example-config.json to config.json to customize."
            )

        # Fall back to SessionConfig defaults
        defaults = SessionConfig()
        return {
            "num_trials": str(defaults.num_trials),
            "trials_per_effort": str(defaults.trials_per_effort),
            "wait_baseline": str(defaults.wait_baseline),
            "wait_breaks": str(defaults.wait_breaks),
            "wait_endline": str(defaults.wait_endline),
        }

    def handler(self):
        terminated = False
        while not terminated:
            event = pygame.event.wait()
            if event.type == pygame.QUIT:
                pygame.quit()
                raise SystemExit("Window closed by user")
            if event.type == pygame.MOUSEBUTTONDOWN:
                if self.next_button.handle_click(event):
                    terminated = True
            self.user_input.handle_event(event)
            self.session_input.handle_event(event)
            # rendering
            self.screen.fill(self.screen_color)
            self.user_input.draw()
            self.session_input.draw()
            self.next_button.draw()
            self.title_box.draw()
            pygame.display.flip()

        user_vals = self.user_input.get_values()
        session_vals = self.session_input.get_values()

        def to_int(val):
            """Convert string to int, raising ValueError on failure."""
            try:
                return int(val)
            except (TypeError, ValueError) as e:
                raise ValueError(f"Invalid integer value: {val}") from e

        session_cfg = SessionConfig(
            num_trials=to_int(session_vals["num_trials"]),
            trials_per_effort=to_int(session_vals["trials_per_effort"]),
            wait_baseline=to_int(session_vals["wait_baseline"]),
            wait_breaks=to_int(session_vals["wait_breaks"]),
            wait_endline=to_int(session_vals["wait_endline"]),
        )
        user_info = UserInfo(
            name=user_vals["name"] or "anon",
            last_name=user_vals["last_name"] or "anon",
            mobile=user_vals["mobile"],
            age=to_int(user_vals["age"]) if user_vals["age"] else None,
            gender=user_vals["gender"],
        )
        return user_info, session_cfg


if __name__ == "__main__":
    pygame.init()
    screen = pygame.display.set_mode((1920, 1080))
    screen_color = (211, 211, 211)
    screen.fill(screen_color)
    signup_page = SignUp(screen, screen_color=screen_color)
    user_info, session_config = signup_page.handler()
    print(user_info)
    print(session_config)
    pygame.quit()
