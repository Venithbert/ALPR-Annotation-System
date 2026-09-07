# ALPR-Annotation-System

## Setup

py -3.12 -m venv .venv

.venv\Scripts\Activate.ps1

pip install -r requirements.txt


## Run

```
python app.py
```

## How it works

The company had a manual workflow for building ground truth data. We automated 80% of it. 

All three agree → automated. Any disagreement → a person reads it.

<img width="1346" height="1072" alt="Screenshot 2026-09-07 091631" src="https://github.com/user-attachments/assets/3996686f-d3e9-4f2b-92bb-44256d4099fc" />


## Background

The approach here is **Query-by-Committee**: run several independent
models and send a sample to a human only where they disagree.

- modAL documentation — practical, code-first intro to committee-based
  disagreement: https://modal-python.readthedocs.io/en/latest/content/models/Committee.html
 
