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

# 대진표 생성 함수
def create_matchups(participants_1):
    females = [m for m in participants_1 if gender_map[m['이름']] == '여']
    males = [m for m in participants_1 if gender_map[m['이름']] == '남']

    # 코트 별 팀을 할당할 빈 리스트
    court_3 = []  # 여자복식 혹은 혼복
    court_4 = []  # 남자복식
    court_5 = []  # 복식

    # 3번 코트: 2:2 여자복식, 여자가 부족하면 혼복
    while len(court_3) < 4 and len(females) >= 2:
        # 여성 두 명을 선택하여 복식팀 구성
        team = sorted([females.pop(0), females.pop(-1)], key=lambda x: x['순위'])
        court_3.append(team)

    if len(court_3) < 2:  # 여자가 부족한 경우, 혼복 팀을 추가
        while len(court_3) < 2 and len(females) > 0 and len(males) > 0:
            # 여성 한 명, 남성 한 명을 선택하여 혼합 팀 구성
            team = sorted([females.pop(0), males.pop(-1)], key=lambda x: x['순위'])
            court_3.append(team)

    # 4번 코트: 2:2 남자 복식
    while len(court_4) < 4 and len(males) >= 2:
        # 남성 두 명을 선택하여 복식팀 구성
        team = sorted([males.pop(0), males.pop(-1)], key=lambda x: x['순위'])
        court_4.append(team)

    # 5번 코트: 2:2 복식 (성별에 관계없이)
    all_participants = sorted(participants_1, key=lambda x: x['순위'])
    while len(court_5) < 4 and len(all_participants) >= 4:
        # 순위가 높은 사람과 낮은 사람을 짝지어서 팀을 구성
        team = sorted([all_participants.pop(0), all_participants.pop(-1)], key=lambda x: x['순위'])
        court_5.append(team)

    return court_3, court_4, court_5

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
            extracted_data.append({'순위': rank, '이름': name})

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

        # 매칭 1
        m1_early = [m for m in members_data if m.get('참가') and m.get('일퇴')]
        m1_fill = [m for m in members_data if m.get('참가') and not m.get('늦참') and m not in m1_early]
        random.shuffle(m1_fill)
        participants_1 = (m1_early + m1_fill)[:12]
        participants_1 = sorted(participants_1, key=lambda x: x['순위'])

        # 매칭 2
        p2_set = []

        part_late = [m for m in members_data if m.get('참가') and m.get('늦참')]
        p2_set.extend(part_late)

        part_all = [m for m in members_data if m.get('참가')]
        m1_set = set(id(m) for m in participants_1)
        missing_in_m1 = [m for m in part_all if id(m) not in m1_set]
        for m in missing_in_m1:
            if m not in p2_set:
                p2_set.append(m)

        part_early = [m for m in members_data if m.get('참가') and m.get('일퇴')]
        for m in part_early:
            if m not in p2_set:
                p2_set.append(m)

        needed = 12 - len(p2_set)
        if needed > 0:
            remaining = [m for m in part_all if m not in p2_set]
            random.shuffle(remaining)
            p2_set.extend(remaining[:needed])

        participants_2 = p2_set[:12]
        participants_2 = sorted(participants_2, key=lambda x: x['순위'])

        # 매칭 3
        match3_set = []

        # 1. 참가 + 일퇴
        part_early = [m for m in part_all if m.get('일퇴')]
        match3_set.extend(part_early)

        # 2. 참가 + 늦참
        part_late = [m for m in part_all if m.get('늦참') and m not in match3_set]
        match3_set.extend(part_late)

        # 3. 참가 + 매칭2 제외
        p2_ids = set(id(m) for m in participants_2)
        not_in_p2 = [m for m in part_all if id(m) not in p2_ids and m not in match3_set]
        match3_set.extend(not_in_p2)

        # 4. 부족한 경우 랜덤 충원
        if len(match3_set) < 12:
            remaining = [m for m in part_all if m not in match3_set]
            random.shuffle(remaining)
            match3_set.extend(remaining[:12 - len(match3_set)])

        participants_3 = match3_set[:12]
        participants_3 = sorted(participants_3, key=lambda x: x['순위'])

        # 대진표 생성
        court_3, court_4, court_5 = create_matchups(participants_1)

        return render_template(
            'members.html',
            members=members_data,
            participants_1=participants_1,
            participants_2=participants_2,
            participants_3=participants_3,
            court_3=court_3,
            court_4=court_4,
            court_5=court_5
        )

    return render_template(
        'members.html',
        members=members_data,
        participants_1=[],
        participants_2=[],
        participants_3=[],
        court_3=[],
        court_4=[],
        court_5=[]
    )

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
