from dataclasses import dataclass


@dataclass
class UserInfo:
    name: str
    last_name: str
    mobile: str | None
    age: int | None
    gender: str | None
    # Add validation and methods as needed

    def validate(self) -> None:
        # Add basic validation logic
        if not self.name:
            self.name = "anon"
        if not self.last_name:
            self.last_name = "anon"
        if self.age is not None and (self.age < 0 or self.age > 120):
            raise ValueError("Age must be between 0 and 120.")
        if self.gender is not None and self.gender not in {"M", "F", "NB", "Other", ""}:
            raise ValueError("Gender must be M, F, NB, Other, or blank.")
        # Add more validation as needed
