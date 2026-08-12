# ALPR Annotation System — Architecture

Desktop application (PySide6). 

## Purpose

Measure how accurate the production ALPR is, without reviewing every plate by hand.

Three independent readers vote on each plate. Where all three agree, the result is
accepted automatically. Where they disagree, a human decides. Target: reduce manual
review by 60 to 80 percent. Create ground truth faster without losing quality.

---

## Readers

| Reader | Decoding |
|---|---|
| PaddleOCR | CTC | 
| ParSeq | Autoregressive attention |
| VLM (Qwen 3.5-9B) | Prompted vision-language |

---

## Pipeline

1. **Scan** — list `data/`, sort, parse each filename → one row per image in `results.csv`
2. **Detect** — YOLO per image → padded crop in `crops/`, same filename
3. **Read ×3** — Paddle, then ParSeq, then VLM. Each is a separate subprocess run over
   the whole `crops/` folder, writing its own CSV
4. **Join** — merge the three reader CSVs into `results.csv`, keyed on filename
5. **Normalise** — one shared function applied to all four readings (ALPR + 3 readers)
6. **Vote** — assign a bucket
7. **Review** — operator types the plate for `manual` rows only
8. **Export** — copy images into bucket folders, plus a summary

---

## Bucket rules

| Readers | vs ALPR | Meaning | Bucket |
|---|---|---|---|
| 3/3 agree | matches | ALPR likely correct | `verified` |
| 3/3 agree | differs | ALPR likely wrong | `alpr_error` |
| 2/3 agree | either | uncertain | `manual` |
| no majority | either | uncertain | `manual` |

Special cases:

- A reader that errored or abstained casts no vote. Fewer than three votes means the
  image cannot reach `verified`.
- `no_detection` → `manual`. Readers never see these images.


---

## Folder layout

---

## Code layout

```
alpr/
  core/            no PySide6 imports, ever
    dataset.py     folder → image records, filename parsing
    detect.py      YOLO wrapper
    readers.py     launches reader subprocesses
    vote.py        normalisation + bucket assignment
    store.py       results.csv read/write
  ui/              Qt widgets only
    main_window.py
  config.py
  app.py           entry point
```

---

## Design rules

**`core/` never imports PySide6. `ui/` never contains logic.**
 

---

## Confidence scores

---