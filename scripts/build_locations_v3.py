# -*- coding: utf-8 -*-
"""Build the offline place index; polygons are deliberately discarded."""

import csv
import json
import sys


csv.field_size_limit(1_000_000_000)


def main(source, target):
    records = []
    with open(source, "r", encoding="utf-8-sig", newline="") as source_file:
        for row in csv.DictReader(source_file):
            coordinate = row["geo"].strip()
            if not coordinate or coordinate == "EMPTY":
                continue
            longitude, latitude = coordinate.split()
            records.append({
                "id": row["id"], "pid": row["pid"], "level": int(row["deep"]),
                "name": row["name"], "path": row["ext_path"],
                "longitude": round(float(longitude), 6),
                "latitude": round(float(latitude), 6),
            })
    with open(target, "w", encoding="utf-8") as target_file:
        json.dump(records, target_file, ensure_ascii=False, separators=(",", ":"))
    print(f"wrote {len(records)} places to {target}")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit("usage: build_locations_v3.py source.csv target.json")
    main(sys.argv[1], sys.argv[2])
