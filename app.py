"""Entry point. The ModelScope deployspec pins this filename, so it stays at the root.

Everything it does lives in apps/studio/studio.py. The library sits under src/, so a plain
`python app.py` from a checkout puts it on the path itself instead of requiring an install.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from apps.studio.studio import demo, main  # noqa: E402

if __name__ == "__main__":
    main()
