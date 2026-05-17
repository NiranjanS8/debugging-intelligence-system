from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.projections.service import ProjectionService


def main() -> None:
    service = ProjectionService()
    stats = service.process_pending()
    print(
        f"Processed {stats['processed']} queued projection task(s): "
        f"{stats['succeeded']} succeeded, {stats['failed']} failed."
    )


if __name__ == "__main__":
    main()
