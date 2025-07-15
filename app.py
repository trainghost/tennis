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
    for m in members:
        m.setdefault("late", False)

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
    elif sort == "late_first":
        members.sort(key=lambda x: not x.get("late", False))
    elif sort == "late_last":
        members.sort(key=lambda x: x.get("late", False))


    return render_template("index.html", members=members, sort=sort)



@app.route("/toggle/<int:idx>/<key>")
def toggle(idx, key):
    members = load_data()
    if key in ["tuesday", "thursday", "participated", "late"]:
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
    members = load_data()

    courts = []
    used_names = set()

    # 1. 3번 코트 - 여자 중심
    female = [m for m in members if m["gender"] == "여" and m.get("participated") and not m.get("late", False)]

    if len(female) >= 4:
        # 여자만 4명 이상이면 여자끼리 구성
        female_sorted = sorted(female, key=lambda x: x["rank"])
        teamA = [female_sorted[0], female_sorted[-1]]
        teamB = [female_sorted[1], female_sorted[-2]]
    elif 2 <= len(female) <= 3:
        # 여자 + 남자 혼합, 성별 다르게, 순위 비슷하게
        others = [m for m in members if m.get("participated") and not m.get("late", False) and m["name"] not in [f["name"] for f in female]]
        candidates = female + others
        candidates = sorted(candidates, key=lambda x: x["rank"])
        teamA, teamB = [], []
        for c in candidates:
            if len(teamA) < 2:
                if not teamA or teamA[0]["gender"] != c["gender"]:
                    teamA.append(c)
            elif len(teamB) < 2:
                if not teamB or teamB[0]["gender"] != c["gender"]:
                    teamB.append(c)
            if len(teamA) == 2 and len(teamB) == 2:
                break
    else:
        # 여자 1명 이하 → 전체 참여자 중에서 4명 선택 (성별 무관)
        candidates = [m for m in members if m.get("participated") and not m.get("late", False)]
        candidates = sorted(candidates, key=lambda x: x["rank"])
        teamA = [candidates[0], candidates[-1]]
        teamB = [candidates[1], candidates[-2]]

    courts.append(("3번 코트", teamA, teamB))
    used_names.update(m["name"] for m in teamA + teamB)

    # 2. 4번, 5번 코트 - 남자 중심
    male = [m for m in members if m["gender"] == "남" and m.get("participated") and not m.get("late", False)]
    male = [m for m in male if m["name"] not in used_names]
    male_sorted = sorted(male, key=lambda x: x["rank"])

    if len(male_sorted) >= 4:
        A = [male_sorted[0], male_sorted[-1]]
        B = [male_sorted[1], male_sorted[-2]]
        courts.append(("4번 코트", A, B))
        used_names.update(m["name"] for m in A + B)

    remain = [m for m in male_sorted if m["name"] not in used_names]
    if len(remain) >= 4:
        A = [remain[0], remain[-1]]
        B = [remain[1], remain[-2]]
        courts.append(("5번 코트", A, B))

    return render_template("matches.html", courts=courts)



if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
