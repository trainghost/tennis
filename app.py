from flask import Flask, render_template, request, redirect, url_for
import json
import itertools
import os

app = Flask(__name__)
DATA_FILE = "members_data.json"

def load_members():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, encoding="utf-8") as f:
            return json.load(f)
    return []

def get_ranked_names(members):
    return [f"{m['name']}({m['rank']})" for m in members]

def best_match_pairs(members):
    min_diff = float('inf')
    best_pair = ([], [])
    for comb in itertools.combinations(members, 4):
        for teamA in itertools.combinations(comb, 2):
            teamB = [m for m in comb if m not in teamA]
            sumA = sum(m['rank'] for m in teamA)
            sumB = sum(m['rank'] for m in teamB)
            diff = abs(sumA - sumB)
            if diff < min_diff:
                min_diff = diff
                best_pair = (list(teamA), list(teamB))
    return best_pair

def best_gender_mixed_pairs(members):
    min_diff = float('inf')
    best_pair = ([], [])
    for comb in itertools.combinations(members, 4):
        genders = [m['gender'] for m in comb]
        if genders.count("여") < 2:
            continue
        for teamA in itertools.combinations(comb, 2):
            teamB = [m for m in comb if m not in teamA]
            if len(set(m['gender'] for m in teamA)) != 2:
                continue
            if len(set(m['gender'] for m in teamB)) != 2:
                continue
            sumA = sum(m['rank'] for m in teamA)
            sumB = sum(m['rank'] for m in teamB)
            diff = abs(sumA - sumB)
            if diff < min_diff:
                min_diff = diff
                best_pair = (list(teamA), list(teamB))
    return best_pair

def assign_court(court_name, candidates, used_list, mixed_required=True, only_male=False):
    available = [m for m in candidates if m not in used_list]
    if len(available) < 4:
        return f"{court_name}: 인원 부족", []

    if only_male:
        available = [m for m in available if m['gender'] == '남']
        if len(available) < 4:
            return f"{court_name}: 남자 인원 부족", []
        teamA, teamB = best_match_pairs(available)
    else:
        female_count = len([m for m in available if m['gender'] == '여'])
        if mixed_required and female_count >= 2:
            teamA, teamB = best_gender_mixed_pairs(available)
        else:
            teamA, teamB = best_match_pairs(available)

    used_list.extend(teamA + teamB)
    return f"{court_name}: {', '.join(get_ranked_names(teamA))} vs {', '.join(get_ranked_names(teamB))}", teamA + teamB

def generate_match_text(members):
    participants = [m for m in members if m.get("participated")]
    total_count = len(participants)
    male_count = len([m for m in participants if m['gender'] == '남'])
    female_count = len([m for m in participants if m['gender'] == '여'])

    text = f"참여 인원: 총 {total_count}명 (남자 {male_count}명 / 여자 {female_count}명)\n\n"

    def build_match(title, candidate_order):
        output = f"\n✅ {title}\n"
        used = []
        result, team = assign_court("3번 코트", candidate_order, used)
        output += result + "\n"
        result, team = assign_court("4번 코트", candidate_order, used)
        output += result + "\n"
        result, team = assign_court("5번 코트", candidate_order, used, mixed_required=False, only_male=True)
        output += result + "\n"
        rested = [m['name'] for m in participants if m not in used]
        output += "👋 쉬는 사람: " + (", ".join(rested) if rested else "없음") + "\n"
        return output, used

    match1_used = []
    females = [m for m in participants if m["gender"] == "여"]
    if len(females) >= 4:
        teamA, teamB = best_match_pairs(females)
    elif 2 <= len(females) <= 3:
        teamA, teamB = best_gender_mixed_pairs(participants)
    else:
        teamA, teamB = best_match_pairs(participants)
    match1_used.extend(teamA + teamB)
    text += "✅ 매칭 1 (06:10 ~ 06:35)\n"
    text += "3번 코트: " + ", ".join(get_ranked_names(teamA)) + " vs " + ", ".join(get_ranked_names(teamB)) + "\n"

    for court in ["4번 코트", "5번 코트"]:
        remaining = [m for m in participants if m not in match1_used]
        if len(remaining) >= 4:
            female_remain = [m for m in remaining if m["gender"] == "여"]
            if len(female_remain) >= 2:
                teamA, teamB = best_gender_mixed_pairs(remaining)
            else:
                teamA, teamB = best_match_pairs(remaining)
            match1_used.extend(teamA + teamB)
            text += f"{court}: {', '.join(get_ranked_names(teamA))} vs {', '.join(get_ranked_names(teamB))}\n"
        else:
            text += f"{court}: 인원 부족\n"

    rested1 = [m for m in participants if m not in match1_used]
    text += "👋 쉬는 사람: " + (", ".join(m["name"] for m in rested1) if rested1 else "없음") + "\n"

    match2_candidates = rested1 + [m for m in participants if m not in rested1]
    match2_text, match2_used = build_match("매칭 2 (06:37 ~ 07:00)", match2_candidates)
    text += match2_text

    rested3_priority1 = [m for m in participants if m not in match2_used]
    rested3_priority2 = [m for m in rested1 if m not in rested3_priority1]
    rested3_others = [m for m in participants if m not in rested3_priority1 + rested3_priority2]
    match3_candidates = rested3_priority1 + rested3_priority2 + rested3_others
    match3_text, _ = build_match("매칭 3 (07:00 ~ 07:25)", match3_candidates)
    text += match3_text

    return text

@app.route("/")
def index():
    members = load_members()
    match_text = generate_match_text(members)
    return render_template("index.html", match_text=match_text)

if __name__ == "__main__":
    app.run(debug=True)
