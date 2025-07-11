from flask import Flask, render_template, request, redirect, url_for
import json
import os

app = Flask(__name__)
DATA_FILE = "members_data.json"

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, encoding="utf-8") as f:
            return json.load(f)
    return []

def save_data(members):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(members, f, indent=2, ensure_ascii=False)

@app.route("/", methods=["GET", "POST"])
def index():
    members = load_data()
    if request.method == "POST":
        name = request.form["name"].strip()
        gender = request.form["gender"]
        rank = int(request.form["rank"] or 0)
        members.append({
            "name": name,
            "gender": gender,
            "rank": rank,
            "tuesday": False,
            "thursday": False,
            "participated": False
        })
        save_data(members)
        return redirect(url_for("index"))
    return render_template("index.html", members=members)

@app.route("/toggle/<int:idx>/<key>")
def toggle(idx, key):
    members = load_data()
    if key in ["tuesday", "thursday", "participated"]:
        members[idx][key] = not members[idx].get(key, False)
    save_data(members)
    return redirect(url_for("index"))

@app.route("/delete/<int:idx>")
def delete(idx):
    members = load_data()
    if 0 <= idx < len(members):
        del members[idx]
    save_data(members)
    return redirect(url_for("index"))

@app.route("/generate")
def generate_match():
    import itertools
    members = [m for m in load_data() if m["participated"]]
    def best_match(members):
        min_diff = float("inf")
        best = ([], [])
        for comb in itertools.combinations(members, 4):
            for teamA in itertools.combinations(comb, 2):
                teamB = [m for m in comb if m not in teamA]
                diff = abs(sum(m["rank"] for m in teamA) - sum(m["rank"] for m in teamB))
                if diff < min_diff:
                    min_diff = diff
                    best = (list(teamA), list(teamB))
        return best
    courts = []
    used = set()
    for i in range(3, 6):
        remain = [m for m in members if m["name"] not in used]
        if len(remain) < 4: break
        A, B = best_match(remain)
        used.update(m["name"] for m in A + B)
        courts.append((f"{i}번 코트", A, B))
    return render_template("matches.html", courts=courts)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
