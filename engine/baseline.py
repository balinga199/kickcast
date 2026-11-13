"""
Phase 1: Baseline football prediction engine (no API key needed).

Data: free historical CSVs from football-data.co.uk
Model: team attack/defence strengths updated after every match,
       converted to win/draw/loss probabilities with a Poisson grid.
Backtest: walks forward in time. Each match is predicted BEFORE
          the model sees its result, so the accuracy is honest.

Run:  python baseline.py
"""
import csv
import io
import math
import urllib.request
from datetime import datetime

LEAGUE = "E0"  # E0 = English Premier League. Others: SP1, D1, I1, F1
SEASONS = ["2122", "2223", "2324", "2425", "2526", "2627"]
BACKTEST_FROM = "2324"  # seasons before this only warm up the model

K = 0.06          # how fast team strengths react to new results
HOME_GOALS = 1.5  # league average home goals (updated as we go)
AWAY_GOALS = 1.2  # league average away goals
MAX_GOALS = 8


def fetch_season(season):
    url = f"https://www.football-data.co.uk/mmz4281/{season}/{LEAGUE}.csv"
    try:
        raw = urllib.request.urlopen(url, timeout=30).read().decode("utf-8-sig")
    except Exception as e:
        print(f"  skip {season}: {e}")
        return []
    rows = []
    for r in csv.DictReader(io.StringIO(raw)):
        if not r.get("FTHG") or not r.get("HomeTeam"):
            continue
        d = r["Date"]
        fmt = "%d/%m/%Y" if len(d.split("/")[-1]) == 4 else "%d/%m/%y"
        rows.append({
            "date": datetime.strptime(d, fmt),
            "season": season,
            "home": r["HomeTeam"],
            "away": r["AwayTeam"],
            "hg": int(r["FTHG"]),
            "ag": int(r["FTAG"]),
        })
    return rows


def poisson(k, lam):
    return math.exp(-lam) * lam ** k / math.factorial(k)


def outcome_probs(lam_h, lam_a):
    ph = pd = pa = 0.0
    for i in range(MAX_GOALS + 1):
        for j in range(MAX_GOALS + 1):
            p = poisson(i, lam_h) * poisson(j, lam_a)
            if i > j:
                ph += p
            elif i == j:
                pd += p
            else:
                pa += p
    total = ph + pd + pa
    return ph / total, pd / total, pa / total


class Model:
    def __init__(self):
        self.att = {}
        self.dfn = {}
        self.mu_h = HOME_GOALS
        self.mu_a = AWAY_GOALS

    def _get(self, team):
        return self.att.setdefault(team, 1.0), self.dfn.setdefault(team, 1.0)

    def expected_goals(self, home, away):
        ah, dh = self._get(home)
        aa, da = self._get(away)
        return self.mu_h * ah * da, self.mu_a * aa * dh

    def predict(self, home, away):
        lam_h, lam_a = self.expected_goals(home, away)
        return outcome_probs(lam_h, lam_a), (lam_h, lam_a)

    def update(self, home, away, hg, ag):
        ah, dh = self._get(home)
        aa, da = self._get(away)
        clamp = lambda x: max(0.3, min(3.0, x))
        self.att[home] = clamp(ah + K * (hg / self.mu_h / da - ah))
        self.dfn[away] = clamp(da + K * (hg / self.mu_h / ah - da))
        self.att[away] = clamp(aa + K * (ag / self.mu_a / dh - aa))
        self.dfn[home] = clamp(dh + K * (ag / self.mu_a / aa - dh))
        self.mu_h += 0.002 * (hg - self.mu_h)
        self.mu_a += 0.002 * (ag - self.mu_a)


def actual_outcome(hg, ag):
    return 0 if hg > ag else (1 if hg == ag else 2)  # 0=home 1=draw 2=away


def main():
    print("Downloading data...")
    matches = []
    for s in SEASONS:
        got = fetch_season(s)
        print(f"  {s}: {len(got)} matches")
        matches += got
    matches.sort(key=lambda m: m["date"])
    if not matches:
        print("No data downloaded. Check your internet connection.")
        return

    model = Model()
    n = correct = base_correct = 0
    logloss = 0.0

    for m in matches:
        if m["season"] >= BACKTEST_FROM:
            probs, _ = model.predict(m["home"], m["away"])
            actual = actual_outcome(m["hg"], m["ag"])
            pick = max(range(3), key=lambda i: probs[i])
            n += 1
            correct += pick == actual
            base_correct += actual == 0  # baseline: always pick home win
            logloss += -math.log(max(probs[actual], 1e-9))
        model.update(m["home"], m["away"], m["hg"], m["ag"])

    print("\n=== BACKTEST RESULTS ===")
    print(f"Matches tested : {n}")
    print(f"Model accuracy : {correct / n:.1%}")
    print(f"'Always home'  : {base_correct / n:.1%}  (the number to beat)")
    print(f"Log loss       : {logloss / n:.3f}  (lower is better; ~1.10 = coin flip)")

    print("\nStrongest attacks:")
    for t, v in sorted(model.att.items(), key=lambda x: -x[1])[:5]:
        print(f"  {t}: {v:.2f}")


if __name__ == "__main__":
    main()
