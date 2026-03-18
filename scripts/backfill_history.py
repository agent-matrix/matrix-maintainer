from pathlib import Path
from matrix_maintainer.settings import get_settings

if __name__ == "__main__":
    settings = get_settings()
    Path(settings.state_dir, "history_index.json").write_text("[]", encoding="utf-8")
