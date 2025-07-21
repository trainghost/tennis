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
    if 'file' not in request.files:
        return redirect(request.url)
    file = request.files['file']
    if file.filename == '':
        return redirect(request.url)
    if file:
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
    return "파일 업로드 실패!"


def generate_teams_for_group(participants_list):
    """
    12명의 참여자 리스트와 여성 인원 수에 따라 특정 팀 구성을 반환합니다.
    (이 함수는 메인 로직에서 오버라이드되지 않는 경우에만 사용됩니다. 현재는 사용되지 않습니다.)
    """
    return [] # 이 함수는 직접 호출되지 않으므로 빈 리스트 반환


@app.route('/members', methods=['GET', 'POST'])
def members():
    global members_data

    # 매칭 결과 변수들을 초기화 - GET 요청 시에도 반드시 초기화되어야 합니다.
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
            # Checkboxes are sent as 'on' if checked, otherwise they are not in request.form
            member['매칭1_참여'] = f'match1_{member["이름"]}' in request.form
            member['매칭2_참여'] = f'match2_{member["이름"]}' in request.form
            member['매칭3_참여'] = f'match3_{member["이름"]}' in request.form
            
            # Update rank from dropdown
           member['순위'] = int(request.form.get(f'rank_{member["이름"]}', member['순위']))

            # 일퇴/늦참도 POST 요청 시에만 업데이트되므로 여기서 처리
            # 이전에 사용된 'participate', 'early', 'late' 대신
            # 매칭별 참여 여부와 일퇴/늦참은 별도의 체크박스로 처리되어야 함.
            # 예를 들어, 각 멤버의 '일퇴'와 '늦참'은 명시적인 폼 필드를 통해 받아야 함.
            # 현재 코드에는 일퇴/늦참을 받는 폼 필드가 명시적으로 없으므로,
            # members_data에 일퇴/늦참 정보가 없다면 아래 로직이 제대로 작동하지 않습니다.
            # 이전 코드에서 f'early_{idx}' in request.form 등으로 받았던 부분을 복원해야 합니다.
            member['일퇴'] = f'early_{idx}' in request.form if request.form.get(f'early_{idx}') else False
            member['늦참'] = f'late_{idx}' in request.form if request.form.get(f'late_{idx}') else False


        # --- 매칭 1 참여자 선정 로직 ---
        # 수정: 매칭1 참가자 필터링 시 '매칭1_참여'가 True인 사람만 고려
        participants_1_all = [p for p in members_data if p.get('매칭1_참여')]
        
        # 일퇴/늦참 로직이 매칭 선택에 영향을 주도록 복원 (GET/POST 모두에서 사용될 수 있도록 초기화 로직 안에 있어야 함)
        m1_early = [m for m in participants_1_all if m.get('일퇴')]
        m1_fill = [m for m in participants_1_all if not m.get('늦참') and m not in m1_early]
        random.shuffle(m1_fill)
        participants_1 = (m1_early + m1_fill)[:12]
        participants_1 = sorted(participants_1, key=lambda x: x['순위'])

        # --- 매칭 2 참여자 선정 로직 ---
        p2_set = []
        part_late = [m for m in members_data if m.get('매칭2_참여') and m.get('늦참')]
        p2_set.extend(part_late)

        part_all_m2 = [m for m in members_data if m.get('매칭2_참여')]
        m1_set = set(id(m) for m in participants_1)
        missing_in_m1 = [m for m in part_all_m2 if id(m) not in m1_set]
        for m in missing_in_m1:
            if m not in p2_set:
                p2_set.append(m)

        part_early_m2 = [m for m in members_data if m.get('매칭2_참여') and m.get('일퇴')]
        for m in part_early_m2:
            if m not in p2_set:
                p2_set.append(m)

        needed = 12 - len(p2_set)
        if needed > 0:
            remaining = [m for m in part_all_m2 if m not in p2_set]
            random.shuffle(remaining)
            p2_set.extend(remaining[:needed])

        participants_2 = p2_set[:12]
        participants_2 = sorted(participants_2, key=lambda x: x['순위'])

        # --- 매칭 3 참여자 선정 로직 ---
        match3_set = []
        part_all_m3 = [m for m in members_data if m.get('매칭3_참여')] # Only consider those marked for Match 3
        
        # 일퇴자 먼저
        early_leave_participants_3 = [m for m in part_all_m3 if m.get('일퇴')]
        match3_set.extend(early_leave_participants_3)

        # 늦참자 다음
        late_participants_3 = [m for m in part_all_m3 if m.get('늦참') and m not in match3_set]
        match3_set.extend(late_participants_3)

        # 매칭1, 매칭2에 참여하지 않은 사람들을 우선 포함
        match1_ids = {id(p) for p in participants_1} # Use id for proper object comparison
        match2_ids = {id(p) for p in participants_2}
        not_in_m1_m2 = [p for p in part_all_m3 if id(p) not in match1_ids and id(p) not in match2_ids and p not in match3_set]
        match3_set.extend(not_in_m1_m2)

        # 12명이 안되면 나머지 매칭3 참여자 중 랜덤하게 채움
        if len(match3_set) < 12:
            remaining = [m for m in part_all_m3 if m not in match3_set]
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

        # --- 각 매칭에 대한 팀 생성 함수 호출 (기본 로직) ---
        # 매칭 1 대진표 (오버라이드 로직 포함)
        if summary_1['total'] == 12:
            female_members_1 = sorted([p for p in participants_1 if p['성별'] == '여'], key=lambda x: x['순위'])
            male_members_1 = sorted([p for p in participants_1 if p['성별'] == '남'], key=lambda x: x['순위'])

            if summary_1['female'] == 5 and summary_1['male'] == 7:
                team_match_results_1 = [
                    {'court': '3번 코트', 'team_a': [female_members_1[1], female_members_1[4]], 'team_b': [female_members_1[2], female_members_1[3]]}, # 여자2위, 여자5위 vs 여자3위, 여자4위
                    {'court': '4번 코트', 'team_a': [female_members_1[0], male_members_1[0]], 'team_b': [male_members_1[5], male_members_1[6]]}, # 여자1위, 남자1위 vs 남자6위, 남자7위
                    {'court': '5번 코트', 'team_a': [male_members_1[1], male_members_1[4]], 'team_b': [male_members_1[2], male_members_1[3]]}  # 남자2위, 남자5위 vs 남자3위, 남자4위
                ]
            elif summary_1['female'] == 4 and summary_1['male'] == 8:
                team_match_results_1 = [
                    {'court': '3번 코트', 'team_a': [female_members_1[0], female_members_1[3]], 'team_b': [female_members_1[1], female_members_1[2]]}, # 여자1위, 여자4위 vs 여자2위, 여자3위
                    {'court': '4번 코트', 'team_a': [male_members_1[0], male_members_1[7]], 'team_b': [male_members_1[1], male_members_1[6]]}, # 남자1위, 남자8위 vs 남자2위, 남자7위
                    {'court': '5번 코트', 'team_a': [male_members_1[2], male_members_1[5]], 'team_b': [male_members_1[3], male_members_1[4]]}  # 남자3위, 남자6위 vs 남자4위, 남자5위
                ]
            elif summary_1['female'] == 3 and summary_1['male'] == 9:
                team_match_results_1 = [
                    {'court': '3번 코트', 'team_a': [female_members_1[0], male_members_1[0]], 'team_b': [male_members_1[7], male_members_1[8]]}, # 여자1위, 남자1위 vs 남자8위, 남자9위
                    {'court': '4번 코트', 'team_a': [female_members_1[1], male_members_1[1]], 'team_b': [female_members_1[2], male_members_1[2]]}, # 여자2위, 남자2위 vs 여자3위, 남자3위
                    {'court': '5번 코트', 'team_a': [male_members_1[3], male_members_1[6]], 'team_b': [male_members_1[4], male_members_1[5]]}  # 남자4위, 남자7위 vs 남자5위, 남자6위
                ]
            elif summary_1['female'] == 2 and summary_1['male'] == 10:
                team_match_results_1 = [
                    {'court': '3번 코트', 'team_a': [female_members_1[0], male_members_1[0]], 'team_b': [female_members_1[1], male_members_1[1]]}, # 여자1위, 남자1위 vs 여자2위, 남자2위
                    {'court': '4번 코트', 'team_a': [male_members_1[2], male_members_1[9]], 'team_b': [male_members_1[3], male_members_1[8]]}, # 남자3위, 남자10위 vs 남자4위, 남자9위
                    {'court': '5번 코트', 'team_a': [male_members_1[4], male_members_1[7]], 'team_b': [male_members_1[5], male_members_1[6]]}  # 남자5위, 남자8위 vs 남자6위, 남자7위
                ]
            elif summary_1['female'] == 1 and summary_1['male'] == 11:
                team_match_results_1 = [
                    {'court': '3번 코트', 'team_a': [female_members_1[0], male_members_1[0]], 'team_b': [male_members_1[9], male_members_1[10]]}, # 여자1위, 남자1위 vs 남자10위, 남자11위
                    {'court': '4번 코트', 'team_a': [male_members_1[1], male_members_1[8]], 'team_b': [male_members_1[2], male_members_1[7]]}, # 남자2위, 남자9위 vs 남자3위, 남자8위
                    {'court': '5번 코트', 'team_a': [male_members_1[3], male_members_1[6]], 'team_b': [male_members_1[4], male_members_1[5]]}  # 남자4위, 남자7위 vs 남자5위, 남자6위
                ]
            elif summary_1['female'] == 0 and summary_1['male'] == 12:
                team_match_results_1 = [
                    {'court': '3번 코트', 'team_a': [male_members_1[0], male_members_1[11]], 'team_b': [male_members_1[1], male_members_1[10]]}, # 남자1위, 남자12위 vs 남자2위, 남자11위
                    {'court': '4번 코트', 'team_a': [male_members_1[2], male_members_1[9]], 'team_b': [male_members_1[3], male_members_1[8]]}, # 남자3위, 남자10위 vs 남자4위, 남자9위
                    {'court': '5번 코트', 'team_a': [male_members_1[4], male_members_1[7]], 'team_b': [male_members_1[5], male_members_1[6]]}  # 남자5위, 남자8위 vs 남자6위, 남자7위
                ]

        # 매칭 2 대진표 (오버라이드 로직 포함)
        if summary_2['total'] == 12:
            female_members_2 = sorted([p for p in participants_2 if p['성별'] == '여'], key=lambda x: x['순위'])
            male_members_2 = sorted([p for p in participants_2 if p['성별'] == '남'], key=lambda x: x['순위'])

            if summary_2['female'] == 5 and summary_2['male'] == 7:
                team_match_results_2 = [
                    {'court': '3번 코트', 'team_a': [female_members_2[0], male_members_2[0]], 'team_b': [female_members_2[1], male_members_2[1]]}, # 여자1위, 남자1위 vs 여자2위, 남자2위
                    {'court': '4번 코트', 'team_a': [female_members_2[2], male_members_2[2]], 'team_b': [female_members_2[3], male_members_2[3]]}, # 여자3위, 남자3위 vs 여자4위, 남자4위
                    {'court': '5번 코트', 'team_a': [female_members_2[4], male_members_2[4]], 'team_b': [male_members_2[5], male_members_2[6]]}  # 여자5위, 남자5위 vs 남자6위, 남자7위
                ]
            elif summary_2['female'] == 4 and summary_2['male'] == 8:
                team_match_results_2 = [
                    {'court': '3번 코트', 'team_a': [male_members_2[0], female_members_2[0]], 'team_b': [male_members_2[1], female_members_2[1]]}, # 남자1위, 여자1위 vs 남자2위, 여자2위
                    {'court': '4번 코트', 'team_a': [male_members_2[2], female_members_2[2]], 'team_b': [male_members_2[3], female_members_2[3]]}, # 남자3위, 여자3위 vs 남자4위, 여자4위
                    {'court': '5번 코트', 'team_a': [male_members_2[4], male_members_2[7]], 'team_b': [male_members_2[5], male_members_2[6]]}  # 남자5위, 남자8위 vs 남자6위, 남자7위
                ]
            elif summary_2['female'] == 3 and summary_2['male'] == 9:
                team_match_results_2 = [
                    {'court': '3번 코트', 'team_a': [female_members_2[1], male_members_2[0]], 'team_b': [male_members_2[5], male_members_2[7]]}, # 여자2위, 남자1위 vs 남자6위, 남자8위
                    {'court': '4번 코트', 'team_a': [female_members_2[0], male_members_2[1]], 'team_b': [female_members_2[2], male_members_2[2]]}, # 여자1위, 남자2위 vs 여자3위, 남자3위
                    {'court': '5번 코트', 'team_a': [male_members_2[3], male_members_2[8]], 'team_b': [male_members_2[4], male_members_2[6]]}  # 남자4위, 남자9위 vs 남자5위, 남자7위
                ]
            elif summary_2['female'] == 2 and summary_2['male'] == 10:
                team_match_results_2 = [
                    {'court': '3번 코트', 'team_a': [female_members_2[0], male_members_2[1]], 'team_b': [female_members_2[1], male_members_2[3]]}, # 여자1위, 남자2위 vs 여자2위, 남자4위
                    {'court': '4번 코트', 'team_a': [male_members_2[0], male_members_2[7]], 'team_b': [male_members_2[1], male_members_2[6]]}, # 남자1위, 남자8위 vs 남자2위, 남자7위
                    {'court': '5번 코트', 'team_a': [male_members_2[4], male_members_2[9]], 'team_b': [male_members_2[5], male_members_2[8]]}  # 남자5위, 남자10위 vs 남자6위, 남자9위
                ]
            elif summary_2['female'] == 1 and summary_2['male'] == 11:
                team_match_results_2 = [
                    {'court': '3번 코트', 'team_a': [female_members_2[0], male_members_2[1]], 'team_b': [male_members_2[8], male_members_2[10]]}, # 여자1위, 남자2위 vs 남자9위, 남자11위
                    {'court': '4번 코트', 'team_a': [male_members_2[0], male_members_2[9]], 'team_b': [male_members_2[2], male_members_2[5]]}, # 남자1위, 남자10위 vs 남자3위, 남자6위
                    {'court': '5번 코트', 'team_a': [male_members_2[3], male_members_2[7]], 'team_b': [male_members_2[4], male_members_2[6]]}  # 남자4위, 남자8위 vs 남자5위, 남자7위
                ]
            elif summary_2['female'] == 0 and summary_2['male'] == 12:
                team_match_results_2 = [
                    {'court': '3번 코트', 'team_a': [male_members_2[0], male_members_2[10]], 'team_b': [male_members_2[1], male_members_2[9]]}, # 남자1위, 남자11위 vs 남자2위, 남자10위
                    {'court': '4번 코트', 'team_a': [male_members_2[2], male_members_2[8]], 'team_b': [male_members_2[3], male_members_2[7]]}, # 남자3위, 남자9위 vs 남자4위, 남자8위
                    {'court': '5번 코트', 'team_a': [male_members_2[4], male_members_2[11]], 'team_b': [male_members_2[5], male_members_2[6]]}  # 남자5위, 남자12위 vs 남자6위, 남자7위
                ]

        # 매칭 3 대진표 (오버라이드 로직 포함)
        if summary_3['total'] == 12:
            female_members_3 = sorted([p for p in participants_3 if p['성별'] == '여'], key=lambda x: x['순위'])
            male_members_3 = sorted([p for p in participants_3 if p['성별'] == '남'], key=lambda x: x['순위'])

            if summary_3['female'] == 5 and summary_3['male'] == 7:
                team_match_results_3 = [
                    {'court': '3번 코트', 'team_a': [male_members_3[1], female_members_3[3]], 'team_b': [male_members_3[3], female_members_3[0]]}, # 남자2위, 여자4위 vs 남자4위, 여자1위
                    {'court': '4번 코트', 'team_a': [male_members_3[0], female_members_3[4]], 'team_b': [male_members_3[6], female_members_3[2]]}, # 남자1위, 여자5위 vs 남자7위, 여자3위
                    {'court': '5번 코트', 'team_a': [female_members_3[1], male_members_3[2]], 'team_b': [male_members_3[4], male_members_3[5]]}  # 여자2위, 남자3위 vs 남자5위, 남자6위
                ]
            elif summary_3['female'] == 4 and summary_3['male'] == 8:
                team_match_results_3 = [
                    {'court': '3번 코트', 'team_a': [male_members_3[5], female_members_3[0]], 'team_b': [male_members_3[4], female_members_3[1]]}, # 남자6위, 여자1위 vs 남자5위, 여자2위
                    {'court': '4번 코트', 'team_a': [male_members_3[7], female_members_3[2]], 'team_b': [male_members_3[6], female_members_3[3]]}, # 남자8위, 여자3위 vs 남자7위, 여자4위
                    {'court': '5번 코트', 'team_a': [male_members_3[0], male_members_3[3]], 'team_b': [male_members_3[1], male_members_3[2]]}  # 남자1위, 남자4위 vs 남자2위, 남자3위
                ]
            elif summary_3['female'] == 3 and summary_3['male'] == 9:
                team_match_results_3 = [
                    {'court': '3번 코트', 'team_a': [female_members_3[2], male_members_3[0]], 'team_b': [male_members_3[6], male_members_3[7]]}, # 여자3위, 남자1위 vs 남자7위, 남자8위
                    {'court': '4번 코트', 'team_a': [female_members_3[1], male_members_3[1]], 'team_b': [female_members_3[0], male_members_3[2]]}, # 여자2위, 남자2위 vs 여자1위, 남자3위
                    {'court': '5번 코트', 'team_a': [male_members_3[3], male_members_3[5]], 'team_b': [male_members_3[4], male_members_3[8]]}  # 남자4위, 남자6위 vs 남자5위, 남자9위
                ]
            elif summary_3['female'] == 2 and summary_3['male'] == 10:
                team_match_results_3 = [
                    {'court': '3번 코트', 'team_a': [male_members_3[0], female_members_3[0]], 'team_b': [male_members_3[1], female_members_3[1]]}, # 남자1위, 여자1위 vs 남자2위, 여자2위
                    {'court': '4번 코트', 'team_a': [male_members_3[2], male_members_3[8]], 'team_b': [male_members_3[3], male_members_3[7]]}, # 남자3위, 남자9위 vs 남자4위, 남자8위
                    {'court': '5번 코트', 'team_a': [male_members_3[4], male_members_3[9]], 'team_b': [male_members_3[5], male_members_3[6]]}  # 남자5위, 남자10위 vs 남자6위, 남자7위
                ]
            elif summary_3['female'] == 1 and summary_3['male'] == 11:
                team_match_results_3 = [
                    {'court': '3번 코트', 'team_a': [female_members_3[0], male_members_3[2]], 'team_b': [male_members_3[8], male_members_3[9]]}, # 여자1위, 남자3위 vs 남자9위, 남자10위
                    {'court': '4번 코트', 'team_a': [male_members_3[1], male_members_3[10]], 'team_b': [male_members_3[3], male_members_3[7]]}, # 남자2위, 남자11위 vs 남자4위, 남자8위
                    {'court': '5번 코트', 'team_a': [male_members_3[4], male_members_3[6]], 'team_b': [male_members_3[0], male_members_3[5]]}  # 남자5위, 남자7위 vs 남자1위, 남자6위
                ]
            elif summary_3['female'] == 0 and summary_3['male'] == 12:
                team_match_results_3 = [
                    {'court': '3번 코트', 'team_a': [male_members_3[0], male_members_3[9]], 'team_b': [male_members_3[1], male_members_3[8]]}, # 남자1위, 남자10위 vs 남자2위, 남자9위
                    {'court': '4번 코트', 'team_a': [male_members_3[2], male_members_3[7]], 'team_b': [male_members_3[3], male_members_3[6]]}, # 남자3위, 남자8위 vs 남자4위, 남자7위
                    {'court': '5번 코트', 'team_a': [male_members_3[4], male_members_3[11]], 'team_b': [male_members_3[5], male_members_3[10]]}  # 남자5위, 남자12위 vs 남자6위, 남자11위
                ]

    # Ensure all variables are passed to the template in both GET and POST
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
