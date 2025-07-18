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

    def make_team5(female_top, male_top, others):
        # 팀A: female_top + male_top
        # 팀B: others 2명
        teamA = [female_top, male_top]
        teamB = others
        return [teamA, teamB]

    if match_no == 1:
        if len(females) >= 5:
            female_top = females.pop(0)
            male_top = males.pop(0) if males else None

            team5 = [female_top]
            if male_top:
                team5.append(male_top)

            # 남자 추가 2명 or 여자 보충
            if len(males) >= 2:
                others = pick(males, 2)
            else:
                others = males
                males.clear()
                needed = 2 - len(others)
                if needed > 0:
                    others += pick(females, needed)

            # 3번 코트 여자복식 4명
            c3 = pick(females, 4)
            # 4번 코트 남자복식 4명
            c4 = pick(males, 4)

            courts[3] = make_teams(c3)
            courts[4] = make_teams(c4)
            courts[5] = make_team5(female_top, male_top, others)

        elif len(females) == 4:
            courts[3] = make_teams(pick(females, 4))
            courts[4] = make_teams(pick(males, 4))
            courts[5] = make_teams(pick(males, 4))

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

    elif match_no == 2:
        if len(females) >= 5:
            # 3,4번 코트에 들어갈 혼복 선수 제외하기 위해 복사
            f_copy = females[:]
            m_copy = males[:]

            # 3번 코트: 여자 1,2위 + 남자 1,2위
            c3_players = f_copy[:2] + m_copy[:2]
            # 4번 코트: 여자 3,4위 + 남자 3,4위
            c4_players = f_copy[2:4] + m_copy[2:4]

            # 선수 리스트에서 3,4번 코트 선수 제거
            for p in c3_players + c4_players:
                if p in f_copy:
                    f_copy.remove(p)
                if p in m_copy:
                    m_copy.remove(p)

            # 5번 코트 팀 구성: 여자 2위 + 남자 2위가 같은 팀
            female_2nd = females[1]
            male_2nd = males[1] if len(males) > 1 else None

            team5 = [female_2nd]
            if male_2nd:
                team5.append(male_2nd)

            # 나머지 2명은 남자 우선으로 채우기
            others = []
            if len(m_copy) >= 2:
                others = pick(m_copy, 2)
            else:
                others = m_copy
                m_copy.clear()
                needed = 2 - len(others)
                if needed > 0:
                    others += pick(f_copy, needed)

            courts[3] = make_teams(c3_players)
            courts[4] = make_teams(c4_players)
            courts[5] = make_team5(female_2nd, male_2nd, others)

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

    else:  # match_no == 3
        if len(females) >= 5:
            f_copy = females[:]
            m_copy = males[:]

            # 3번 코트: 여자 1,2위 + 남자 1,2위
            c3_players = f_copy[:2] + m_copy[:2]
            # 4번 코트: 여자 3,4위 + 남자 3,4위
            c4_players = f_copy[2:4] + m_copy[2:4]

            # 선수 리스트에서 3,4번 코트 선수 제거
            for p in c3_players + c4_players:
                if p in f_copy:
                    f_copy.remove(p)
                if p in m_copy:
                    m_copy.remove(p)

            female_3rd = females[2]
            male_3rd = males[2] if len(males) > 2 else None

            team5 = [female_3rd]
            if male_3rd:
                team5.append(male_3rd)

            others = []
            if len(m_copy) >= 2:
                others = pick(m_copy, 2)
            else:
                others = m_copy
                m_copy.clear()
                needed = 2 - len(others)
                if needed > 0:
                    others += pick(f_copy, needed)

            courts[3] = make_teams(c3_players)
            courts[4] = make_teams(c4_players)
            courts[5] = make_team5(female_3rd, male_3rd, others)

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
