#!/usr/bin/env python3
from __future__ import annotations

import json

from mathfoundry.indexing import db_path, index_all_raw


def main() -> None:
    count = index_all_raw()
    print(json.dumps({"indexed_rows": count, "db": str(db_path())}))


if __name__ == "__main__":
    main()
