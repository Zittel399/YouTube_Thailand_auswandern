"""
Protokolliert jeden kostenpflichtigen API-Lauf (Dauer, geschätzte Kosten)
als eine JSON-Zeile in logs/runs.jsonl. Grundlage für ein späteres
Kosten-/Performance-Dashboard über alle Projekte.

Bewusst NICHT gespeichert: fal.ai-Media-URLs (darüber wären die Videos
abrufbar) und Secrets. Ausgabedateien nur als Pfad relativ zum Projekt.

Kosten sind Schätzungen nach den Preisangaben der Anbieter (cost_basis
sagt, wie gerechnet wurde). Die echten Beträge stehen im fal.ai-Dashboard
unter 'Usage' und können später damit abgeglichen werden.
"""

import json
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LOG_PATH = ROOT / "logs" / "runs.jsonl"
PROJECT = "parallelwelten"


def log_run(agent, model, clip, duration_s, cost_usd=None, cost_basis="",
            target=None, details=None, outputs=(), status="ok"):
    entry = {
        "timestamp": datetime.now().astimezone().isoformat(timespec="seconds"),
        "project": PROJECT,
        "agent": agent,
        "model": model,
        "clip": clip,
        "target": target,
        "status": status,
        "duration_s": round(duration_s, 1),
        "cost_usd_est": None if cost_usd is None else round(cost_usd, 4),
        "cost_basis": cost_basis,
        "details": details or {},
        "outputs": [str(Path(p).resolve().relative_to(ROOT)).replace("\\", "/")
                    for p in outputs],
    }
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with LOG_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    print(f"Lauf protokolliert: {LOG_PATH.relative_to(ROOT)}")
