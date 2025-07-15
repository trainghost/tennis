import os
import json 
import openpyxl
from flask import Flask, request, redirect, render_template, jsonify, url_for


app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
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

    # GET 요청일 경우 정렬 적용
    sort = request.args.get("sort")
    if sort == "asc":
        members.sort(key=lambda x: x["rank"])
    elif sort == "desc":
        members.sort(key=lambda x: x["rank"], reverse=True)

    return render_template("index.html", members=members, sort=sort)


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

@app.route("/upload", methods=["POST"])
def upload_excel():
    if "file" not in request.files:
        return "No file part", 400
    file = request.files["file"]
    if file.filename == "":
        return "No selected file", 400

    try:
        wb = openpyxl.load_workbook(file)
        sheet = wb.active
        members = load_data()

        for row in sheet.iter_rows(min_row=2, values_only=True):
            name, gender, rank = row[:3]
            members.append({
                "name": name.strip() if isinstance(name, str) else "",
                "gender": gender if gender in ["남", "여"] else "남",
                "rank": int(rank) if isinstance(rank, (int, float)) else 0,
                "tuesday": False,
                "thursday": False,
                "participated": False
            })
        save_data(members)
    except Exception as e:
        return f"파일 처리 중 오류: {str(e)}", 500

    return redirect(url_for("index"))  # ✅ 꼭 있어야 함!

        
@app.route("/update_rank/<int:idx>", methods=["POST"])
def update_rank(idx):
    members = load_data()
    new_rank = int(request.form.get("rank", 0))
    if 0 <= idx < len(members):
        members[idx]["rank"] = new_rank
        save_data(members)
    return redirect(url_for("index"))

@app.route("/", methods=["GET", "POST"])
def index():
    members = load_data()
    sort = request.args.get("sort")

    if sort == "asc":
        members.sort(key=lambda m: m.get("rank", 0))
    elif sort == "desc":
        members.sort(key=lambda m: m.get("rank", 0), reverse=True)

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

    return render_template("index.html", members=members, sort=sort)




    filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
    file.save(filepath)

    wb = openpyxl.load_workbook(filepath)
    sheet = wb.active
    new_members = []

    for row in sheet.iter_rows(min_row=2, values_only=True):
        if not row or not row[0]:
            continue
        name = str(row[0]).strip()
        gender = str(row[1]).strip() if len(row) > 1 and row[1] else "남"
        rank = int(row[2]) if len(row) > 2 and row[2] else 0

        new_members.append({
            "name": name,
            "gender": gender if gender in ["남", "여"] else "남",
            "rank": rank,
            "tuesday": False,
            "thursday": False,
            "participated": False
        })

    members = load_data()
    members.extend(new_members)
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
