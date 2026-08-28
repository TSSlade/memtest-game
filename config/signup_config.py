# Moved from vendor/memtest/signup_config.py
from dataclasses import dataclass


@dataclass
class SignUpConfig:
    user_fields: dict[str, str] | None = None
    session_fields: dict[str, str] | None = None

    def __post_init__(self):
        if self.user_fields is None:
            self.user_fields = {
                "name": "First Name",
                "last_name": "Last Name",
                "mobile": "Mobile #",
                "age": "Age",
                "gender": "Gender (M/F/NB)",
            }
        if self.session_fields is None:
            self.session_fields = {
                "num_trials": "# of tasks to attempt",
                "trials_per_effort": "# of tasks before a break",
                "wait_baseline": "Baseline Wait (sec)",
                "wait_breaks": "Breaks Wait (sec)",
                "wait_endline": "Endline Wait (sec)",
            }
