from flask import Flask, render_template, request, redirect, url_for
import pandas as pd
import os
import random
import re

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

members_data = []
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

            gender = gender_map.get(name, '미정')
            extracted_data.append({'순위': rank, '이름': name, '성별': gender})

    global members_data
    members_data = extracted_data

    return redirect(url_for('members'))


# ✅ 추가된 팀 생성 함수
def generate_teams_for_group(participants_list):
    """
    12명의 참여자 리스트를 받아 성별에 따라 팀을 구성하고 코트별 매칭을 반환합니다.
    혼성 조를 우선으로 구성하며, 남은 인원으로 동성 조를 만듭니다.
    """
    if len(participants_list) != 12:
        return [] # 12명이 아니면 팀 생성 안 함

    female_members = sorted([m for m in participants_list if m['성별'] == '여'], key=lambda x: x['순위'])
    male_members = sorted([m for m in participants_list if m['성별'] == '남'], key=lambda x: x['순위'])

    all_pairs = []

    # 1. 혼성 조 (남녀 각각 1명) 우선 구성
    num_mixed_pairs = min(len(female_members), len(male_members))
    for _ in range(num_mixed_pairs):
        all_pairs.append([female_members.pop(0), male_members.pop(0)])
    
    # 2. 남은 여성 멤버들로 여성 조 (여녀 각각 1명) 구성
    while len(female_members) >= 2:
        all_pairs.append([female_members.pop(0), female_members.pop(0)])

    # 3. 남은 남성 멤버들로 남성 조 (남남 각각 1명) 구성
    while len(male_members) >= 2:
        all_pairs.append([male_members.pop(0), male_members.pop(0)])

    # 4. 모든 조가 6개(12명) 인지 확인
    if len(all_pairs) != 6:
        return [] # 팀 구성 오류 또는 12명 아닌 경우

    random.shuffle(all_pairs) # 조를 무작위로 섞어서 코트 배정의 다양성 확보

    # 5. 조를 코트에 배정 (3개 코트, 각 코트 2개 조 = 4명)
    teams_on_courts = []
    for i in range(3): # 3번, 4번, 5번 코트
        if len(all_pairs) >= 2:
            team_a = all_pairs.pop(0) # 첫 번째 조
            team_b = all_pairs.pop(0) # 두 번째 조
            teams_on_courts.append({
                'court': f'{i+3}번 코트',
                'team_a': team_a,
                'team_b': team_b
            })
        else:
            break # 남은 조가 부족하면 중단

    return teams_on_courts


@app.route('/members', methods=['GET', 'POST'])
def members():
    # 매칭 결과 변수들을 초기화
    participants_1 = []
    participants_2 = []
    participants_3 = []
    summary_1 = {'total': 0, 'male': 0, 'female': 0}
    summary_2 = {'total': 0, 'male': 0, 'female': 0}
    summary_3 = {'total': 0, 'male': 0, 'female': 0}
    team_match_results_1 = []
    team_match_results_2 = []
    team_match_results_3 = []


    if request.method == 'POST':
        for idx, member in enumerate(members_data):
            member['참가'] = f'participate_{idx}' in request.form
            member['일퇴'] = f'early_{idx}\' in request.form
            member['늦참'] = f'late_{idx}\' in request.form

        # --- 매칭 1 로직 (기존과 동일) ---
        m1_early = [m for m in members_data if m.get('참가') and m.get('일퇴')]
        m1_fill = [m for m in members_data if m.get('참가') and not m.get('늦참') and m not in m1_early]
        random.shuffle(m1_fill)
        participants_1 = (m1_early + m1_fill)[:12]
        participants_1 = sorted(participants_1, key=lambda x: x['순위'])

        # --- 매칭 2 로직 (기존과 동일) ---
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

        # --- 매칭 3 로직 (기존과 동일) ---
        match3_set = []
        part_early = [m for m in part_all if m.get('일퇴')]
        match3_set.extend(part_early)
        part_late = [m for m in part_all if m.get('늦참') and m not in match3_set]
        match3_set.extend(part_late)
        p2_ids = set(id(m) for m in participants_2)
        not_in_p2 = [m for m in part_all if id(m) not in p2_ids and m not in match3_set]
        match3_set.extend(not_in_p2)
        if len(match3_set) < 12:
            remaining = [m for m in part_all if m not in match3_set]
            random.shuffle(remaining)
            match3_set.extend(remaining[:12 - len(match3_set)])
        participants_3 = match3_set[:12]
        participants_3 = sorted(participants_3, key=lambda x: x['순위'])

        # ✅ 성별 요약 계산 (기존과 동일)
        def count_gender(participants):
            total = len(participants)
            male = sum(1 for p in participants if p.get('성별') == '남')
            female = sum(1 for p in participants if p.get('성별') == '여')
            return {'total': total, 'male': male, 'female': female}

        summary_1 = count_gender(participants_1)
        summary_2 = count_gender(participants_2)
        summary_3 = count_gender(participants_3)

        # --- 각 매칭에 대해 새로운 팀 생성 함수 호출 ---
        team_match_results_1 = generate_teams_for_group(participants_1)
        team_match_results_2 = generate_teams_for_group(participants_2)
        team_match_results_3 = generate_teams_for_group(participants_3)

    return render_template(
        'members.html',
        members=members_data,
        participants_1=participants_1,
        participants_2=participants_2,
        participants_3=participants_3,
        summary_1=summary_1,
        summary_2=summary_2,
        summary_3=summary_3,
        team_match_results_1=team_match_results_1,
        team_match_results_2=team_match_results_2,
        team_match_results_3=team_match_results_3
    )


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)

