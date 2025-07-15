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
    elif sort == "participated_first":
        members.sort(key=lambda x: not x.get("participated", False))  # 참여한 사람 먼저
    elif sort == "participated_last":
        members.sort(key=lambda x: x.get("participated", False))  # 참여 안 한 사람 먼저

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
    file = request.files["file"]
    if file and file.filename.endswith(".xlsx"):
        wb = openpyxl.load_workbook(file)
        sheet = wb.active

        headers = [cell.value for cell in sheet[1]]
        members = []

        for row in sheet.iter_rows(min_row=2, values_only=True):
            data = dict(zip(headers, row))
            members.append({
                "name": data.get("name", "").strip(),
                "gender": data.get("gender", "").strip(),
                "rank": int(data.get("rank", 0) or 0),
                "tuesday": bool(data.get("tuesday")),
                "thursday": bool(data.get("thursday")),
                "participated": bool(data.get("participated"))
            })

        save_data(members)
        return redirect(url_for("index"))

    return "올바른 엑셀 파일(.xlsx)을 업로드하세요.", 400


@app.route("/update_participation", methods=["POST"])
def update_participation():
    members = load_data()
    for i, member in enumerate(members):
        checkbox_name = f"participated_{i}"
        member["participated"] = checkbox_name in request.form
    save_data(members)
    return redirect(url_for("index"))

        
@app.route("/update_rank/<int:idx>", methods=["POST"])
def update_rank(idx):
    members = load_data()
    new_rank = int(request.form.get("rank", 0))
    if 0 <= idx < len(members):
        members[idx]["rank"] = new_rank
        save_data(members)
    return redirect(url_for("index"))

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
    members = [m for m in load_data() if m.get("participated")]

    # 늦게 시작한 사람 제외 (기능이 있다면 적용)
    for m in members:
        if "late" not in m:
            m["late"] = False  # 기본값 설정

    courts = []
    used_names = set()

    def best_team_split(players):
        import itertools
        min_diff = float("inf")
        best = ([], [])
        for teamA in itertools.combinations(players, 2):
            teamB = [p for p in players if p not in teamA]
            diff = abs(sum(p["rank"] for p in teamA) - sum(p["rank"] for p in teamB))
            if diff < min_diff:
                min_diff = diff
                best = (list(teamA), teamB)
        return best

    # 3번 코트 (여자 우선 or 혼합)
    females = [m for m in members if m["gender"] == "여" and not m.get("late") and m["name"] not in used_names]

    if len(females) >= 4:
        females = sorted(females, key=lambda x: x["rank"])
        selected = females[:4]
    elif 2 <= len(females) <= 3:
        others = [m for m in members if m["name"] not in used_names and m not in females and not m.get("late")]
        selected = (females + others)[:4]
    else:
        selected = [m for m in members if m["name"] not in used_names and not m.get("late")] [:4]

    if len(selected) == 4:
        A, B = best_team_split(selected)
        courts.append(("3번 코트", A, B))
        used_names.update(m["name"] for m in A + B)

    # 남자만 대상
    males = [m for m in members if m["gender"] == "남" and not m.get("late") and m["name"] not in used_names]
    males = sorted(males, key=lambda x: x["rank"])

    if len(males) >= 8:
        selected = males[:8]
    else:
        selected = males

    if len(selected) >= 4:
        # 4번 코트
        teamA = [selected[0], selected[-1]]
        teamB = [selected[1], selected[-2]]
        courts.append(("4번 코트", teamA, teamB))
        used_names.update(m["name"] for m in teamA + teamB)

    remain = [m for m in males if m["name"] not in used_names]
    if len(remain) >= 4:
        teamA = [remain[0], remain[-1]]
        teamB = [remain[1], remain[-2]]
        courts.append(("5번 코트", teamA, teamB))
        used_names.update(m["name"] for m in teamA + teamB)

    return render_template("matches.html", courts=courts)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
