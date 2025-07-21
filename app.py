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
    '독고혁': '남', '이성훈': '남', '이종욱': '남', '테스': '남', '오리': '여'
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
            extracted_data.append({'순위': rank, '김나연': name, '성별': gender}) # Corrected '이름' key
    
    # Fix: Ensure '이름' is the key used for names
    for member in extracted_data:
        if '김나연' in member: # Check if the incorrect key exists
            member['이름'] = member.pop('김나연') # Rename it to '이름'


    global members_data
    members_data = extracted_data

    return redirect(url_for('members'))


def generate_teams_for_group(participants_list):
    """
    12명의 참여자 리스트와 여성 인원 수에 따라 특정 팀 구성을 반환합니다.
    """
    if len(participants_list) != 12:
        return [] # 12명이 아니면 팀 생성 안 함

    female_members = sorted([m for m in participants_list if m['성별'] == '여'], key=lambda x: x['순위'])
    male_members = sorted([m for m in participants_list if m['성별'] == '남'], key=lambda x: x['순위'])

    female_count = len(female_members)
    male_count = len(male_members)

    team_match_results = []

    # 여성 5명 (남성 7명) - (이것은 매칭1,3에 기본 적용되는 배치입니다. 매칭2는 별도 오버라이드)
    if female_count == 5 and male_count == 7:
        if len(female_members) >= 5 and len(male_members) >= 7:
            team_match_results = [
                {
                    'court': '3번 코트',
                    'team_a': [female_members[1], female_members[4]], # 여자2위, 여자5위
                    'team_b': [female_members[2], female_members[3]]  # 여자3위, 여자4위
                },
                {
                    'court': '4번 코트',
                    'team_a': [female_members[0], male_members[0]], # 여자1위, 남자1위
                    'team_b': [male_members[5], male_members[6]]    # 남자6위, 남자7위
                },
                {
                    'court': '5번 코트',
                    'team_a': [male_members[1], male_members[4]], # 남자2위, 남자5위
                    'team_b': [male_members[2], male_members[3]]  # 남자3위, 남자4위
                }
            ]
    # 여성 4명 (남성 8명) - (이것은 매칭1,3에 기본 적용되는 배치입니다. 매칭2는 별도 오버라이드)
    elif female_count == 4 and male_count == 8:
        if len(female_members) >= 4 and len(male_members) >= 8:
            team_match_results = [
                {
                    'court': '3번 코트',
                    'team_a': [female_members[0], female_members[3]], # 여자1위, 여자4위
                    'team_b': [female_members[1], female_members[2]]  # 여자2위, 여자3위
                },
                {
                    'court': '4번 코트',
                    'team_a': [male_members[0], male_members[7]], # 남자1위, 남자8위
                    'team_b': [male_members[1], male_members[6]]  # 남자2위, 남자7위
                },
                {
                    'court': '5번 코트',
                    'team_a': [male_members[2], male_members[5]], # 남자3위, 남자6위
                    'team_b': [male_members[3], male_members[4]]  # 남자4위, 남자5위
                }
            ]
    # 여성 3명 (남성 9명)
    elif female_count == 3 and male_count == 9:
        if len(female_members) >= 3 and len(male_members) >= 9:
            team_match_results = [
                {
                    'court': '3번 코트',
                    'team_a': [female_members[0], male_members[0]], # 여자1위, 남자1위
                    'team_b': [male_members[7], male_members[8]]    # 남자8위, 남자9위
                },
                {
                    'court': '4번 코트',
                    'team_a': [female_members[1], male_members[1]], # 여자2위, 남자2위
                    'team_b': [female_members[2], male_members[2]]  # 여자3위, 남자3위
                },
                {
                    'court': '5번 코트',
                    'team_a': [male_members[3], male_members[6]], # 남자4위, 남자7위
                    'team_b': [male_members[4], male_members[5]]  # 남자5위, 남자6위
                }
            ]
    # 여성 2명 (남성 10명)
    elif female_count == 2 and male_count == 10:
        if len(female_members) >= 2 and len(male_members) >= 10:
            team_match_results = [
                {
                    'court': '3번 코트',
                    'team_a': [female_members[0], male_members[0]], # 여자1위, 남자1위
                    'team_b': [female_members[1], male_members[1]]  # 여자2위, 남자2위
                },
                {
                    'court': '4번 코트',
                    'team_a': [male_members[2], male_members[9]], # 남자3위, 남자10위
                    'team_b': [male_members[3], male_members[8]]  # 남자4위, 남자9위
                },
                {
                    'court': '5번 코트',
                    'team_a': [male_members[4], male_members[7]], # 남자5위, 남자8위
                    'team_b': [male_members[5], male_members[6]]  # 남자6위, 남자7위
                }
            ]
    # 여성 1명 (남성 11명)
    elif female_count == 1 and male_count == 11:
        if len(female_members) >= 1 and len(male_members) >= 11:
            team_match_results = [
                {
                    'court': '3번 코트',
                    'team_a': [female_members[0], male_members[0]], # 여자1위, 남자1위
                    'team_b': [male_members[9], male_members[10]]   # 남자10위, 남자11위
                },
                {
                    'court': '4번 코트',
                    'team_a': [male_members[1], male_members[8]], # 남자2위, 남자9위
                    'team_b': [male_members[2], male_members[7]]  # 남자3위, 남자8위
                },
                {
                    'court': '5번 코트',
                    'team_a': [male_members[3], male_members[6]], # 남자4위, 남자7위
                    'team_b': [male_members[4], male_members[5]]  # 남자5위, 남자6위
                }
            ]
    # 여성 0명 (남성 12명)
    elif female_count == 0 and male_count == 12:
        if len(male_members) >= 12:
            team_match_results = [
                {
                    'court': '3번 코트',
                    'team_a': [male_members[0], male_members[11]], # 남자1위, 남자12위
                    'team_b': [male_members[1], male_members[10]]  # 남자2위, 남자11위
                },
                {
                    'court': '4번 코트',
                    'team_a': [male_members[2], male_members[9]], # 남자3위, 남자10위
                    'team_b': [male_members[3], male_members[8]]  # 남자4위, 남자9위
                },
                {
                    'court': '5번 코트',
                    'team_a': [male_members[4], male_members[7]], # 남자5위, 남자8위
                    'team_b': [male_members[5], male_members[6]]  # 남자6위, 남자7위
                }
            ]
    
    return team_match_results


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
            member['일퇴'] = f'early_{idx}' in request.form
            member['늦참'] = f'late_{idx}' in request.form

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

        # ✅ 성별 요약 계산
        def count_gender(participants):
            total = len(participants)
            male = sum(1 for p in participants if p.get('성별') == '남')
            female = sum(1 for p in participants if p.get('성별') == '여')
            return {'total': total, 'male': male, 'female': female}

        summary_1 = count_gender(participants_1)
        summary_2 = count_gender(participants_2)
        summary_3 = count_gender(participants_3)

        # --- 각 매칭에 대해 팀 생성 함수 호출 (기본 로직) ---
        team_match_results_1 = generate_teams_for_group(participants_1)
        team_match_results_2 = generate_teams_for_group(participants_2)
        team_match_results_3 = generate_teams_for_group(participants_3)

        # ✅ 매칭2에 대한 여성 5명 특정 오버라이드 로직
        if summary_2['total'] == 12:
            if summary_2['female'] == 5:
                female_members_2 = sorted([m for m in participants_2 if m['성별'] == '여'], key=lambda x: x['순위'])
                male_members_2 = sorted([m for m in participants_2 if m['성별'] == '남'], key=lambda x: x['순위'])

                if len(female_members_2) >= 5 and len(male_members_2) >= 7:
                    team_match_results_2 = [
                        {
                            'court': '3번 코트',
                            'team_a': [female_members_2[0], male_members_2[0]], # 여자1위, 남자1위
                            'team_b': [female_members_2[1], male_members_2[1]]  # 여자2위, 남자2위
                        },
                        {
                            'court': '4번 코트',
                            'team_a': [female_members_2[2], male_members_2[2]], # 여자3위, 남자3위
                            'team_b': [female_members_2[3], male_members_2[3]]  # 여자4위, 남자4위
                        },
                        {
                            'court': '5번 코트',
                            'team_a': [female_members_2[4], male_members_2[4]], # 여자5위, 남자5위
                            'team_b': [male_members_2[5], male_members_2[6]]    # 남자6위, 남자7위
                        }
                    ]
                else:
                    team_match_results_2 = [] 
            # ✅ 매칭2에 대한 여성 4명 특정 오버라이드 로직 추가
            elif summary_2['female'] == 4:
                female_members_2 = sorted([m for m in participants_2 if m['성별'] == '여'], key=lambda x: x['순위'])
                male_members_2 = sorted([m for m in participants_2 if m['성별'] == '남'], key=lambda x: x['순위'])

                if len(female_members_2) >= 4 and len(male_members_2) >= 8:
                    team_match_results_2 = [
                        {
                            'court': '3번 코트',
                            'team_a': [male_members_2[0], female_members_2[0]], # 남자1위, 여자1위
                            'team_b': [male_members_2[1], female_members_2[1]]  # 남자2위, 여자2위
                        },
                        {
                            'court': '4번 코트',
                            'team_a': [male_members_2[2], female_members_2[2]], # 남자3위, 여자3위
                            'team_b': [male_members_2[3], female_members_2[3]]  # 남자4위, 여자4위
                        },
                        {
                            'court': '5번 코트',
                            'team_a': [male_members_2[4], male_members_2[7]], # 남자5위, 남자8위
                            'team_b': [male_members_2[5], male_members_2[6]]  # 남자6위, 남자7위
                        }
                    ]
                else:
                    team_match_results_2 = []

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

