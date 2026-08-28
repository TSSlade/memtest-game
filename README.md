# memtest-game

> **A fork of [masoudrahimi39/visual-working-memory-game](https://github.com/masoudrahimi39/visual-working-memory-game)**,
> taken at commit `646b46e381` and MIT licensed by the original author.
>
> This fork adapts the task for use as a stimulus in a physiological research
> protocol: structured baseline / block / break / endline phases, JSON-driven
> configuration, and audio alerts that double as camera synchronisation markers.
> It has diverged substantially and does not track upstream.
>
> See **[MODIFICATIONS.md](MODIFICATIONS.md)** for what changed and why.
> Everything below this line is the original README, retained as-is except for
> the clone URL and run instructions.

---

## Visual working memory game

If you find this repo helpful, please consider giving it a ⭐ to show your support.

### Demo
https://user-images.githubusercontent.com/65596290/178737195-80565633-60ce-4d58-8590-a0c315346da4.mp4


## Installation
1. Clone the repository by running
```php
git clone https://github.com/TSSlade/memtest-game.git
   ```

2. Install dependencies: `python='3.8', pygame='2.1.2', Pandas, NumPy, Matplotlib` by running below:
   ```php
   pip install pygame='2.1.2', Pandas, NumPy, Matplotlib
   ```
4. Run `python -m game.main_game` from the repository root


## Usage
This project serves multiple purposes:
1. **Entertainment**: Play the game for fun and test your visual working memory abilities.
2. **Gameplay and Eye Tracker Data Collection**: The game collects and saves the player's gameplay data, along with eye tracker data when enabled, providing valuable insights for research and analysis.

### New Modular Structure

The codebase is now organized into submodules for improved maintainability:

- `user/`: User-related dataclasses and input logic
- `config/`: Configuration dataclasses for session, game, and sign-up
- `game/`: Core game logic, task classes, and helpers
- `ui/`: UI components (buttons, input boxes, pages)
- `data/`: Data storage and processing utilities

To run the game, use:
```bash
cd vendor/memtest
python -m game.main_game
```

Update your imports to use the new module paths, e.g.:
```python
from user.user_info import UserInfo
from config.session_config import SessionConfig
from game.task import Task
from ui.buttons import NextButton
```


## Features
- **Modular Design**: All major components are separated by concern for easier maintenance and extension.
- **Adjustable Parameters**: Configuration is handled via dataclasses in the `config/` module.
- **Rule-Based Difficulty Adjustment**: The game incorporates a rule-based difficulty adjustment system, ensuring that players are appropriately challenged as they progress through the tasks.
- **Data Storage**: The player's gameplay data is saved in CSV and plk (Pandas DataFrames) files, facilitating data analysis and post-game insights.
- **Structured User Journey**: The task follows a well-structured user journey, guiding players through different pages, including "Welcome," "Sign Up," "Guiding," "Guiding trials," and "Actual Trials."

## About the memory game?
- At the beginning, a 6*6 hexagonal grid is displayed for two seconds, with certain hexagons simultaneously highlighted in yellow (known as "targets") while the rest are white. 
- After two seconds, all the hexagons become white, and the player must recall and click on the exact locations of the targets. 
- Correct and incorrect clicks instantly become green and red, respectively. 
- The player's score is the number of correct clicks divided by the total number of targets in the task.
- A score 1 represents a win, whereas other scores represent a loss.

