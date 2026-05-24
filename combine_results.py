#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
from pathlib import Path
from datetime import datetime
from result import generate_html
from helper_environment import environment

INPUT_DIR = "test_reports"
OUTPUT_FILE = "test.json"

TITLE = "Calibre-Web Tests"
DESCRIPTION = "Systemtests for Calibre-web"


STATUS_MAPPING = {
    "SUCCESS": {
        "status": "PASS",
        "style": "bg-success",
    },
    "FAIL": {
        "status": "FAIL",
        "style": "bg-danger",
    },
    "ERROR": {
        "status": "ERROR",
        "style": "bg-info",
    },
    "SKIP": {
        "status": "SKIP",
        "style": "bg-warning",
    },
}


def format_duration(seconds: float) -> str:
    seconds = int(seconds)

    hours = seconds // 3600
    minutes = (seconds % 3600) // 60

    if hours > 0:
        return f"{hours}h {minutes} min"

    return f"{minutes} min"


def parse_time(time_string: str) -> datetime:
    """
    Wandelt HH:MM:SS in datetime um.
    Datum ist egal.
    """
    return datetime.strptime(time_string, "%H:%M:%S")


def determine_class_style(stats: dict) -> str:
    if stats.get("error", 0) > 0:
        return "errorClass"

    if stats.get("fail", 0) > 0:
        return "failClass"

    return "passClass"


def combine_reports():
    input_path = Path(INPUT_DIR)

    json_files = sorted(input_path.glob("*.json"))

    if not json_files:
        print(f"Keine JSON Dateien in '{INPUT_DIR}' gefunden")
        return

    # Globale Werte
    global_start = None
    global_stop = None

    total_success = 0
    total_failure = 0
    total_error = 0
    total_skip = 0
    total_tests = 0

    total_duration_seconds = 0.0

    summary_per_class = {}
    class_details = []

    class_counter = 1

    for json_file in json_files:
        with open(json_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        for class_name, class_data in data.items():

            start_time = parse_time(class_data["start_time"])
            end_time = parse_time(class_data["end_time"])

            if global_start is None or start_time < global_start:
                global_start = start_time

            if global_stop is None or end_time > global_stop:
                global_stop = end_time

            stats = class_data["stats"]

            total_success += stats.get("pass", 0)
            total_failure += stats.get("fail", 0)
            total_error += stats.get("error", 0)
            total_skip += stats.get("skip", 0)
            total_tests += stats.get("total", 0)

            duration_seconds = float(class_data.get("duration", 0))
            total_duration_seconds += duration_seconds

            short_class_name = class_name.split(".")[-1]

            # Summary-Teil
            summary_per_class[class_name] = {
                "total": stats.get("total", 0),
                "error": stats.get("error", 0),
                "failure": stats.get("fail", 0),
                "skip": stats.get("skip", 0),
                "success": stats.get("pass", 0),
                "duration": format_duration(duration_seconds),
            }

            # Detail-Teil
            cid = f"c{class_counter}"

            header = {
                "style": determine_class_style(stats),
                "desc": short_class_name,
                "count": stats.get("total", 0),
                "Pass": stats.get("pass", 0),
                "fail": stats.get("fail", 0),
                "error": stats.get("error", 0),
                "skip": stats.get("skip", 0),
                "cid": cid,
            }

            tests = []

            test_counter = 1

            for test in class_data.get("tests", []):
                result = test.get("result", "SUCCESS")
                if result == "ERROR":
                    prefix = "et"
                elif result == "FAIL":
                    prefix = "ft"
                elif result == "SKIP":
                    prefix = "st"
                else:
                    prefix = "pt"

                tid = f"{prefix}{class_counter}.{test_counter}"

                mapping = STATUS_MAPPING.get(
                    result,
                    {
                        "status": result,
                        "style": "bg-secondary",
                    },
                )

                tests.append(
                    {
                        "tid": tid,
                        "Class": "hiddenRow",
                        "style": mapping["style"],
                        "desc": test.get("desc", ""),
                        "script": {
                            "id": tid,
                            "output": test.get("output", ""),
                        },
                        "status": mapping["status"],
                    }
                )

                test_counter += 1

            class_details.append(
                {
                    "header": header,
                    "tests": tests,
                }
            )

            class_counter += 1

    # Beispiel-Datum ergänzen
    today = datetime.now().date()

    global_start_dt = datetime.combine(today, global_start.time())
    global_stop_dt = datetime.combine(today, global_stop.time())

    global_start_dt = global_start_dt.replace(microsecond=1)
    global_stop_dt = global_stop_dt.replace(microsecond=1)

    output = [
        TITLE,
        DESCRIPTION,
        {
            "start_time": global_start_dt.isoformat(),
            "status": {
                "total": total_tests,
                "error": total_error,
                "failure": total_failure,
                "skip": total_skip,
                "success": total_success,
                "duration": format_duration(total_duration_seconds),
            },
            "stop_time": global_stop_dt.isoformat(),
        },
        summary_per_class,
        class_details,
        environment.get_Environment(),
    ]

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=4, ensure_ascii=False)

    print(f"Ergebnis gespeichert in: {OUTPUT_FILE}")
    generate_html(output)


if __name__ == "__main__":
    combine_reports()