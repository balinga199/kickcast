import csv
import io
import json
import os
import urllib.request
from datetime import datetime, timezone

import baseline

FIXTURES_URL = "https://www.football-data.co.uk/fixtures.csv"
LABELS = ["Home win", "Draw", "Away win"]


def load_fixtures():
    raw = urllib.request.urlopen(FIXTURES_URL, timeout=30).read().decode("utf-8-sig")
    rows = []
    for r in csv.DictReader(io.StringIO(raw)):
        if r.get("Div") == baseline.LEAGUE and r.get("HomeTeam"):
            rows.append(r)
    return rows


def main():
    matches = []
    for s in baseline.SEASONS:
        matches += baseline.fetch_season(s)
    matches.sort(key=lambda m: m["date"])

    model = baseline.Model()
    for m in matches:
        model.update(m["home"], m["away"], m["hg"], m["ag"])

    preds = []
    for f in load_fixtures():
        home, away = f["HomeTeam"], f["AwayTeam"]
        probs, (lam_h, lam_a) = model.predict(home, away)
        pick = max(range(3), key=lambda i: probs[i])
        preds.append({
            "date": f["Date"],
            "time": f.get("Time", ""),
            "home": home,
            "away": away,
            "p_home": round(probs[0], 3),
            "p_draw": round(probs[1], 3),
            "p_away": round(probs[2], 3),
            "xg_home": round(lam_h, 2),
            "xg_away": round(lam_a, 2),
            "pick": LABELS[pick],
            "confidence": round(probs[pick], 3),
        })

    os.makedirs("data", exist_ok=True)
    out = {
        "generated": datetime.now(timezone.utc).isoformat(),
        "league": baseline.LEAGUE,
        "predictions": preds,
    }
    with open("data/predictions.json", "w") as fh:
        json.dump(out, fh, indent=2)
    print(f"Saved {len(preds)} predictions")


if __name__ == "__main__":
    main()
