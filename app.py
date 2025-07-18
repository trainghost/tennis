from flask import Flask, render_template, request, redirect, url_for
import pandas as pd
import os
import random
import re

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

members_data = []

# ✅ 이름 → 성별 매핑
gender_map = {
    '장다민': '여', '양승하': '남', '류재리': '여', '우원석': '남',
    '남상훈': '남', '강민구': '남', '임예지': '여', '이준희': '남',
    '박대우': '남', '박소현': '여', '감사': '남', '나석훈': '남',
    '임동민': '남', '박은지': '여', '이재현': '남', '김나연': '여',
    '독고혁': '남', '이성훈': '남', '이종욱': '남', '테스': '남'
}

@app.route('/')
def index():
    return render_template('upload.html')

@app.route('/upload', methods=['POST'])
def upload():
    file = request.files['file']
    filepath = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(filepath)

    df_raw = pd.read_excel(filepath, header=None, usecols=[0])
    extracted_data = []
    for row in df_raw.itertuples(index=False):
        cell = str(row[0]).strip()
        match = re.match(r'(\d+)\.\s*(.+)', cell)
        if match:
            rank = int(match.group(1))
            name = match.group(2).strip()
            gender = gender_map.get(name, '남')
            extracted_data.append({'순위': rank, '이름': name, '성별': gender})

    global members_data
    members_data = extracted_data

    return redirect(url_for('members'))

@app.route('/members', methods=['GET', 'POST'])
def members():
    if request.method == 'POST':
        for idx, member in enumerate(members_data):
            member['참가'] = f'participate_{idx}' in request.form
            member['일퇴'] = f'early_{idx}' in request.form
            member['늦참'] = f'late_{idx}' in request.form

        # ✅ 전체 참가자
        all_participants = [m for m in members_data if m.get('참가')]

        # ✅ 매칭1 (일퇴 우선 → 늦참 제외자 랜덤)
        m1_early = [m for m in all_participants if m.get('일퇴')]
        m1_fill = [m for m in all_participants if not m.get('늦참') and m not in m1_early]
        random.shuffle(m1_fill)
        participants_1 = (m1_early + m1_fill)[:12]
        participants_1 = sorted(participants_1, key=lambda x: x['순위'])
        m1_ids = set(id(m) for m in participants_1)

        # ✅ 매칭2 (늦참 → 일퇴 → 매칭1 제외자 → 랜덤)
        p2_set = [m for m in all_participants if m.get('늦참')]
        p2_set += [m for m in all_participants if m.get('일퇴') and m not in p2_set]
        p2_set += [m for m in all_participants if id(m) not in m1_ids and m not in p2_set]
        if len(p2_set) < 12:
            remaining = [m for m in all_participants if m not in p2_set]
            random.shuffle(remaining)
            p2_set += remaining[:12 - len(p2_set)]
        participants_2 = sorted(p2_set[:12], key=lambda x: x['순위'])
        m2_ids = set(id(m) for m in participants_2)

        # ✅ 매칭3 (늦참 → 일퇴 → 매칭1,2 제외자 → 랜덤)
        p3_set = [m for m in all_participants if m.get('늦참')]
        p3_set += [m for m in all_participants if m.get('일퇴') and m not in p3_set]
        p3_set += [m for m in all_participants if id(m) not in m1_ids and id(m) not in m2_ids and m not in p3_set]
        if len(p3_set) < 12:
            remaining = [m for m in all_participants if m not in p3_set]
            random.shuffle(remaining)
            p3_set += remaining[:12 - len(p3_set)]
        participants_3 = sorted(p3_set[:12], key=lambda x: x['순위'])

        # ✅ 코트 배정
        courts_1 = generate_court_assignments(participants_1, 1)
        courts_2 = generate_court_assignments(participants_2, 2)
        courts_3 = generate_court_assignments(participants_3, 3)

        return render_template(
            'members.html',
            members=members_data,
            participants_1=participants_1,
            participants_2=participants_2,
            participants_3=participants_3,
            courts_1=courts_1,
            courts_2=courts_2,
            courts_3=courts_3
        )

    return render_template(
        'members.html',
        members=members_data,
        participants_1=[],
        participants_2=[],
        participants_3=[],
        courts_1={},
        courts_2={},
        courts_3={}
    )

# ✅ 코트 배정 로직
def generate_court_assignments(players, match_no):
    assigned = set()
    courts = {3: [], 4: [], 5: []}

    females = sorted([p for p in players if p['성별'] == '여'], key=lambda x: x['순위'])
    males = sorted([p for p in players if p['성별'] == '남'], key=lambda x: x['순위'])

    def pick_from_list(lst, count):
        selected = []
        for p in lst:
            if id(p) not in assigned and len(selected) < count:
                selected.append(p)
        for p in selected:
            assigned.add(id(p))
        return selected

    def make_teams(four_players):
        sp = sorted(four_players, key=lambda x: x['순위'])
        return [[sp[0], sp[3]], [sp[1], sp[2]]]

    def make_mixed_teams(fem_list, mal_list):
        fem_selected = pick_from_list(fem_list, 2)
        mal_selected = pick_from_list(mal_list, 2)
        if len(fem_selected) < 2 or len(mal_selected) < 2:
            remain = pick_from_list(fem_list + mal_list, 4)
            return make_teams(remain)
        else:
            return make_teams(fem_selected + mal_selected)

    if match_no == 1:
        if len(females) >= 5:
            # 3번: 여자복식 (여자 4명)
            c3 = pick_from_list(females, 4)
            # 4번: 남자복식 (남자 4명)
            c4 = pick_from_list(males, 4)
            # 5번: 여자 1위 포함 + 남자 3명 혼합 복식
            team5 = []
            team5 += pick_from_list(females[:1], 1)  # 여자 1위 포함
            team5 += pick_from_list(males, 3)
            # 부족하면 여자 추가
            if len(team5) < 4:
                team5 += pick_from_list(females, 4 - len(team5))
            courts[3] = make_teams(c3)
            courts[4] = make_teams(c4)
            courts[5] = make_teams(team5)
        elif len(females) == 4:
            c3 = pick_from_list(females, 4)  # 여자복식
            c4 = pick_from_list(males, 4)    # 남자복식
            c5 = pick_from_list(males, 4)    # 남자복식
            courts[3] = make_teams(c3)
            courts[4] = make_teams(c4)
            courts[5] = make_teams(c5)
        elif len(females) in [2, 3]:
            c3 = make_mixed_teams(females, males)  # 혼복
            c4 = pick_from_list(males, 4)           # 남자복식
            c5 = pick_from_list(players, 4)          # 성별무관 복식
            courts[3] = c3
            courts[4] = make_teams(c4)
            courts[5] = make_teams(c5)
        else:
            # 여자 1명 이하: 전부 성별무관 복식
            c3 = pick_from_list(players, 4)
            c4 = pick_from_list(players, 4)
            c5 = pick_from_list(players, 4)
            courts[3] = make_teams(c3)
            courts[4] = make_teams(c4)
            courts[5] = make_teams(c5)

    elif match_no == 2:
        if len(females) >= 5:
            c3 = make_mixed_teams(females, males)
            c4 = make_mixed_teams(females, males)
            # 5번: 여자 2위 + 남자 2명 팀 vs 남자 팀 (4명)
            teamA = []
            if len(females) >= 2:
                fem2 = pick_from_list(females[1:], 1)
                teamA.extend(fem2)
            teamA.extend(pick_from_list(males, 2))
            teamB = pick_from_list(males, 4 - len(teamA))
            c5 = teamA + teamB
            if len(c5) < 4:
                c5.extend(pick_from_list(females + males, 4 - len(c5)))
            courts[3] = c3
            courts[4] = c4
            courts[5] = make_teams(c5)
        elif len(females) == 4:
            c3 = make_mixed_teams(females, males)
            c4 = make_mixed_teams(females, males)
            c5 = pick_from_list(males, 4)
            courts[3] = c3
            courts[4] = c4
            courts[5] = make_teams(c5)
        elif len(females) in [2, 3]:
            c3 = make_mixed_teams(females, males)
            c4 = pick_from_list(males, 4)
            c5 = pick_from_list(players, 4)
            courts[3] = c3
            courts[4] = make_teams(c4)
            courts[5] = make_teams(c5)
        else:
            c3 = pick_from_list(players, 4)
            c4 = pick_from_list(players, 4)
            c5 = pick_from_list(players, 4)
            courts[3] = make_teams(c3)
            courts[4] = make_teams(c4)
            courts[5] = make_teams(c5)

    else:  # 매칭3
        if len(females) >= 5:
            c3 = make_mixed_teams(females, males)
            c4 = make_mixed_teams(females, males)
            # 5번: 여자 3위 + 남자 3위 + 남자 1명 (4명)
            team5 = []
            if len(females) >= 3:
                team5.extend(pick_from_list(females[2:], 1))
            team5.extend(pick_from_list(males[2:], 3))
            if len(team5) < 4:
                team5.extend(pick_from_list(females + males, 4 - len(team5)))
            courts[3] = c3
            courts[4] = c4
            courts[5] = make_teams(team5)
        elif len(females) == 4:
            c3 = make_mixed_teams(females, males)
            c4 = make_mixed_teams(females, males)
            c5 = pick_from_list(males, 4)
            courts[3] = c3
            courts[4] = c4
            courts[5] = make_teams(c5)
        elif len(females) in [2, 3]:
            c3 = make_mixed_teams(females, males)
            c4 = pick_from_list(males, 4)
            c5 = pick_from_list(players, 4)
            courts[3] = c3
            courts[4] = make_teams(c4)
            courts[5] = make_teams(c5)
        else:
            c3 = pick_from_list(players, 4)
            c4 = pick_from_list(players, 4)
            c5 = pick_from_list(players, 4)
            courts[3] = make_teams(c3)
            courts[4] = make_teams(c4)
            courts[5] = make_teams(c5)

    return courts



def pick_team(four_players):
    sorted_players = sorted(four_players, key=lambda x: x['순위'])
    return [[sorted_players[0], sorted_players[3]], [sorted_players[1], sorted_players[2]]]

def pick_mixed(females, males):
    if len(females) >= 2 and len(males) >= 2:
        players = [females.pop(0), females.pop(0), males.pop(0), males.pop(0)]
    else:
        players = females[:2] + males[:2]
    return pick_team(players)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
