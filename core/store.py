import csv

def save_records(records, out_path):
    """Write records dict to a CSV."""
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["filename", "alpr_plate"])
        for name, plate in records.items():
            writer.writerow([name, plate])

def save_results(records, detections, out_path):
    """Write scan and detection results to a CSV, joined on filename."""
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["filename", "alpr_plate", "det_confidence"])
        for name, plate in records.items():
            writer.writerow([name, plate, detections.get(name)])