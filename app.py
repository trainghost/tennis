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

    # 매칭 1 처리
    if match_no == 1:
        selected_females = females[:min(5, len(females))]
        selected_males = males[:min(7, len(males))]
        
        selected_players = selected_females + selected_males  # 매칭 1에 선발된 12명

        if len(selected_females) == 5:  # 조건 5: 여자 5명일 경우
            # 3번 코트: 선발된 12명 중 순위 제일 높은 남자와 순위 제일 높은 여자가 팀 vs 순위 제일 낮은 남자 2명
            team_3_1 = [selected_females[0], selected_males[0]]  # 순위 제일 높은 여자와 남자
            team_3_2 = [selected_males[-2], selected_males[-1]]  # 순위 제일 낮은 남자 2명
            courts[3] = [team_3_1, team_3_2]

            # 4번 코트: 선발된 12명 중 순위 두번째 높은 여자와 순위 제일 낮은 여자가 팀 vs 순위 세번째로 높은 여자와 순위 네번째로 높은 여자가 팀
            team_4_1 = [selected_females[1], selected_females[-1]]  # 두 번째로 높은 여자와 제일 낮은 여자
            team_4_2 = [selected_females[2], selected_females[3]]  # 세 번째로 높은 여자와 네 번째로 높은 여자
            courts[4] = [team_4_1, team_4_2]

            # 5번 코트: 남자 복식 (순위 제일 높은 남자와 제일 낮은 남자)
            team_5 = [selected_males[1], selected_males[-3]]  # 남자 4명 중 순위 제일 높은 남자와 제일 낮은 남자
            courts[5] = make_teams(team_5)

        elif len(selected_females) == 4:  # 조건 4: 여자 4명일 경우
            # 3번 코트: 선발된 12명 중 순위 제일 높은 여자와 순위 제일 낮은 여자가 팀 vs 순위 두번째로 높은 여자와 순위 세번째로 높은 여자가 팀
            team_3_1 = [selected_females[0], selected_females[-1]]  # 순위 제일 높은 여자와 제일 낮은 여자
            team_3_2 = [selected_females[1], selected_females[2]]  # 두 번째로 높은 여자와 세 번째로 높은 여자
            courts[3] = [team_3_1, team_3_2]

            # 4번 코트: 남자 복식 (코트에 배정된 4명 중 순위 제일 높은 사람과 제일 낮은 사람이 팀)
            team_4 = pick(selected_males, 4)
            courts[4] = make_teams(team_4)

            # 5번 코트: 남자 복식 (코트에 배정된 4명 중 순위 제일 높은 사람과 제일 낮은 사람이 팀)
            team_5 = pick(selected_males, 4)
            courts[5] = make_teams(team_5)

        elif len(selected_females) == 3:  # 조건 3: 여자 3명일 경우
            # 3번 코트: 선발된 12명 중 순위 제일 높은 남자와 선발된 12명 중 순위 제일 높은 여자가 팀 vs 순위 두 번째로 높은 남자와 선발된 12명 중 순위 두 번째로 높은 여자가 팀
            team_3_1 = [selected_females[0], selected_males[0]]  # 순위 제일 높은 여자와 남자
            team_3_2 = [selected_males[1], selected_females[1]]  # 두 번째로 높은 남자와 여자
            courts[3] = [team_3_1, team_3_2]

            # 4번 코트: 남자 복식 (코트에 배정된 4명 중 순위 제일 높은 사람과 제일 낮은 사람이 팀)
            team_4 = pick(selected_males, 4)
            courts[4] = make_teams(team_4)

            # 5번 코트: 남자 복식 (코트에 배정된 4명 중 순위 제일 높은 사람과 제일 낮은 사람이 팀)
            team_5 = pick(selected_males, 4)
            courts[5] = make_teams(team_5)

        elif len(selected_females) == 2:  # 조건 2: 여자 2명일 경우
            # 3번 코트: 선발된 12명 중 순위 제일 높은 남자와 여자가 팀 vs 선발된 12명 중 제일 순위 낮은 남자 2명
            team_3_1 = [selected_females[0], selected_males[0]]  # 순위 제일 높은 여자와 남자
            team_3_2 = [selected_males[-2], selected_males[-1]]  # 순위 제일 낮은 남자 2명
            courts[3] = [team_3_1, team_3_2]

            # 4번 코트: 남자 복식 (코트에 배정된 4명 중 순위 제일 높은 사람과 제일 낮은 사람이 팀)
            team_4 = pick(selected_males, 4)
            courts[4] = make_teams(team_4)

            # 5번 코트: 남자 복식 (코트에 배정된 4명 중 순위 제일 높은 사람과 제일 낮은 사람이 팀)
            team_5 = pick(selected_males, 4)
            courts[5] = make_teams(team_5)

        elif len(selected_females) == 1:  # 조건 1: 여자 1명일 경우
            # 3번 코트: 남자복식 (순위가 제일 높은 사람과 제일 낮은 사람이 팀)
            team_3 = pick(selected_males, 4)
            courts[3] = make_teams(team_3)

            # 4번 코트: 남자복식 (순위가 제일 높은 사람과 제일 낮은 사람이 팀)
            team_4 = pick(selected_males, 4)
            courts[4] = make_teams(team_4)

            # 5번 코트: 남자복식 (순위가 제일 높은 사람과 제일 낮은 사람이 팀)
            team_5 = pick(selected_males, 4)
            courts[5] = make_teams(team_5)

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
