"""Entry point. The ModelScope deployspec pins this filename, so it stays at the root.

Everything it does lives in apps/studio/studio.py.
"""

from apps.studio.studio import demo, main

if __name__ == "__main__":
    main()
