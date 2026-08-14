import csv
import random

def fake_reader(records, name, out_path):
    """Write a fake reader CSV: mostly correct plates, some deliberate errors.

    Stand-in for a real OCR reader until the models are wired up.
    """
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["filename", "plate", "confidence", "status"])

        for filename, plate in records.items():
            roll = random.random()

            if roll < 0.1:
                writer.writerow([filename, "", "", "error"])
            elif roll < 0.3:
                writer.writerow([filename, plate + "X", 0.55, "ok"])
            else:
                writer.writerow([filename, plate, 0.95, "ok"])