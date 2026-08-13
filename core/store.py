import csv


def save_records(records, out_path):
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["filename", "alpr_plate"])
        for name, plate in records.items():
            writer.writerow([name, plate])