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
        courts_1 = assign_courts(participants_1, 1)
        courts_2 = assign_courts(participants_2, 2)
        courts_3 = assign_courts(participants_3, 3)

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
def assign_courts(players, match_no):
    courts = {3: [], 4: [], 5: []}
    females = sorted([p for p in players if p['성별'] == '여'], key=lambda x: x['순위'])
    males = sorted([p for p in players if p['성별'] == '남'], key=lambda x: x['순위'])

    def pick(lst, n):
        picked = lst[:n]
        del lst[:n]
        return picked

    def make_teams(four):
        sorted_players = sorted(four, key=lambda x: x['순위'])
        return [[sorted_players[0], sorted_players[3]], [sorted_players[1], sorted_players[2]]]

    # -----------------
    if match_no == 1:
        if len(females) >= 5:
            # 여자 1위는 females[0], 남자 1위는 males[0]
            female_top = females.pop(0)
            if males:
                male_top = males.pop(0)
            else:
                male_top = None  # 남자가 없을 수도 있음

            team5 = [female_top]
            if male_top:
                team5.append(male_top)

            # 남자 우선으로 5번 코트 4명 채우기 (여자 1명 + 남자 1명 + 남자 2명 혹은 부족시 여자 보충)
            if len(males) >= 2:
                team5 += pick(males, 2)
            else:
                # 남자 부족하면 남자 다 넣고 여자 보충
                team5 += males
                males.clear()
                needed = 4 - len(team5)
                if needed > 0:
                    team5 += pick(females, needed)

            # 3번 코트: 여자복식 4명
            c3 = pick(females, 4)

            # 4번 코트: 남자복식 4명
            c4 = pick(males, 4)

            courts[3] = make_teams(c3)
            courts[4] = make_teams(c4)
            courts[5] = make_teams(team5)

        elif len(females) == 4:
            courts[3] = make_teams(pick(females, 4))  # 여복
            courts[4] = make_teams(pick(males, 4))    # 남복
            courts[5] = make_teams(pick(males, 4))    # 남복

        elif len(females) in [2, 3]:
            mixed = females[:2] + males[:2]
            courts[3] = make_teams(mixed)
            males = males[2:]
            courts[4] = make_teams(pick(males, 4))
            remaining = players[8:12]
            courts[5] = make_teams(remaining)

        else:
            courts[3] = make_teams(players[:4])
            courts[4] = make_teams(players[4:8])
            courts[5] = make_teams(players[8:12])

    # -----------------
    elif match_no == 2:
        if len(females) >= 5:
            # 3,4번 혼복
            mixed1 = females[:2] + males[:2]
            courts[3] = make_teams(mixed1)
            mixed2 = females[2:4] + males[2:4]
            courts[4] = make_teams(mixed2)
            # 5번: 여자 2위 + 남자 2위 + 남자 2명
            team5 = []
            if len(females) >= 2:
                team5.append(females[1])
            if len(males) >= 2:
                team5.append(males[1])
            team5 += pick(males[4:], 2)
            courts[5] = make_teams(team5)

        elif len(females) == 4:
            courts[3] = make_teams(females[:2] + males[:2])
            courts[4] = make_teams(females[2:] + males[2:4])
            courts[5] = make_teams(pick(males[4:], 4))

        elif len(females) in [2, 3]:
            courts[3] = make_teams(females[:2] + males[:2])
            courts[4] = make_teams(pick(males[2:], 4))
            courts[5] = make_teams(players[8:12])

        else:
            courts[3] = make_teams(players[:4])
            courts[4] = make_teams(players[4:8])
            courts[5] = make_teams(players[8:12])

    # -----------------
    else:  # match_no == 3
        if len(females) >= 5:
            courts[3] = make_teams(females[:2] + males[:2])
            courts[4] = make_teams(females[2:4] + males[2:4])
            team5 = []
            if len(females) >= 3:
                team5.append(females[2])
            if len(males) >= 3:
                team5.append(males[2])
            team5 += pick(males[4:], 2)
            courts[5] = make_teams(team5)

        elif len(females) == 4:
            courts[3] = make_teams(females[:2] + males[:2])
            courts[4] = make_teams(females[2:] + males[2:4])
            courts[5] = make_teams(pick(males[4:], 4))

        elif len(females) in [2, 3]:
            courts[3] = make_teams(females[:2] + males[:2])
            courts[4] = make_teams(pick(males[2:], 4))
            courts[5] = make_teams(players[8:12])

        else:
            courts[3] = make_teams(players[:4])
            courts[4] = make_teams(players[4:8])
            courts[5] = make_teams(players[8:12])

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
