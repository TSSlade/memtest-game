# Moved from vendor/memtest/session_config.py
from dataclasses import dataclass


@dataclass
class SessionConfig:
    num_trials: int = 40
    trials_per_effort: int = 10
    wait_baseline: int = 60
    wait_breaks: int = 15
    wait_endline: int = 120

    def validate(self) -> None:
        if self.num_trials <= 0:
            raise ValueError("num_trials must be positive.")
        if self.trials_per_effort <= 0:
            raise ValueError("trials_per_effort must be positive.")
        if self.wait_baseline < 0 or self.wait_breaks < 0 or self.wait_endline < 0:
            raise ValueError("Wait times must be non-negative.")

    def to_dict(self) -> dict:
        """Export configuration to dictionary."""
        return {
            "num_trials": self.num_trials,
            "trials_per_effort": self.trials_per_effort,
            "wait_baseline": self.wait_baseline,
            "wait_breaks": self.wait_breaks,
            "wait_endline": self.wait_endline,
        }

    @classmethod
    def from_dict(cls, data: dict) -> SessionConfig:
        """Create SessionConfig from dictionary, using defaults for missing keys."""
        defaults = cls()
        return cls(
            num_trials=data.get("num_trials", defaults.num_trials),
            trials_per_effort=data.get("trials_per_effort", defaults.trials_per_effort),
            wait_baseline=data.get("wait_baseline", defaults.wait_baseline),
            wait_breaks=data.get("wait_breaks", defaults.wait_breaks),
            wait_endline=data.get("wait_endline", defaults.wait_endline),
        )
