from flask import Flask, render_template, request, redirect, url_for
import pandas as pd
import os
import random
import re

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

members_data = []
# ✅ '오리'님 성별 '여'로 추가
gender_map = {
    '장다민': '여', '양승하': '남', '류재리': '여', '우원석': '남',
    '남상훈': '남', '강민구': '남', '임예지': '여', '이준희': '남',
    '박대우': '남', '박소현': '여', '감사': '남', '나석훈': '남',
    '임동민': '남', '박은지': '여', '이재현': '남', '김나연': '여',
    '독고혁': '남', '이성훈': '남', '이종욱': '남', '테스': '남', '오리': '여'
}


@app.route('/')
def index():
    # 'upload.html'이 있어야 파일 업로드 시작 페이지가 제대로 표시됩니다.
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
            # 정규표현식으로 '순위. 이름' 패턴 매칭
            match = re.match(r'(\d+)\.\s*(.+)', cell)
            if match:
                rank = int(match.group(1))
                name = match.group(2).strip()

                # gender_map에서 성별 조회, 없으면 '미정'
                gender = gender_map.get(name, '미정')
                extracted_data.append({'순위': rank, '이름': name, '성별': gender}) # '이름' 키로 저장


        global members_data
        members_data = extracted_data
        
        # 파일 업로드 후 members 페이지로 리다이렉트
        return redirect(url_for('members'))
    return "파일 업로드 실패!"


# 모든 매칭에 대한 기본 팀 생성 로직 (오버라이드 전에 사용)
def generate_teams_for_group(participants_list):
    """
    12명의 참여자 리스트에 대해 기본 팀 구성을 반환합니다.
    (오버라이드 로직이 적용되지 않을 때 사용됩니다.)
    """
    if len(participants_list) != 12:
        return [] # 12명이 아니면 팀 생성 안 함

    female_members = sorted([m for m in participants_list if m['성별'] == '여'], key=lambda x: x['순위'])
    male_members = sorted([m for m in participants_list if m['성별'] == '남'], key=lambda x: x['순위'])

    team_match_results = []
    
    # 기본적인 팀 구성 로직 (여성 참여자 수에 관계없이 남은 인원으로 매칭)
    # 이 부분은 여성 인원별 오버라이드 로직이 더 우선순위를 가집니다.
    # 여기서는 예시로 일반적인 남녀 혼합 매칭을 하나만 구성해봅니다.
    # 실제로는 이 함수가 직접 호출되기보다는, 각 매칭별 if/elif 문에서
    # 특정 인원수 조합에 대한 오버라이드가 우선 적용되고,
    # 그렇지 않을 경우 랜덤 또는 다른 기본 로직이 적용되게 됩니다.
    
    # 여기서는 오버라이드 로직이 명확히 정의된 경우에만 대진표를 생성하도록 비워두거나,
    # 아니면 일반적인 랜덤 매칭 로직을 넣을 수 있습니다.
    # 현재는 오버라이드되지 않는 모든 케이스를 고려하지 않고, 특정 케이스만 정의하므로
    # 이 함수 자체는 비워두거나, 더 복잡한 기본 매칭 로직을 포함해야 합니다.
    # 기존 코드의 흐름을 유지하기 위해 특정 인원수에 대한 오버라이드를 main 함수에 두겠습니다.

    return team_match_results


@app.route('/members', methods=['GET', 'POST'])
def members():
    global members_data # members_data는 전역 변수로 사용

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
            member['매칭1_참여'] = request.form.get(f'match1_{member["이름"]}') == 'on'
            member['매칭2_참여'] = request.form.get(f'match2_{member["이름"]}') == 'on'
            member['매칭3_참여'] = request.form.get(f'match3_{member["이름"]}') == 'on'
            
            # 순위는 드롭다운에서 선택된 값으로 업데이트
            member['순위'] = int(request.form.get(f'rank_{member["이름"]}'))

        # --- 매칭 1 참여자 선정 로직 ---
        participants_1 = [p for p in members_data if p.get('매칭1_참여')]
        # 매칭1은 총 12명으로 고정하고, 일퇴/늦참에 따른 우선순위가 없으므로 단순히 참가자 중 12명을 선택.
        # 기존 로직을 따르되, 일퇴/늦참은 매칭1에서는 직접적인 참여자 필터링에 사용되지 않는 것으로 해석
        # (이전 코드에서 m1_early, m1_fill이 있었지만, 최종적으로 participants_1은 12명으로 고정)
        random.shuffle(participants_1) # 순서는 랜덤으로 섞음
        participants_1 = sorted(participants_1[:12], key=lambda x: x['순위']) # 상위 12명만 선택하고 순위로 정렬


        # --- 매칭 2 참여자 선정 로직 ---
        # 매칭2는 매칭1에서 빠진 사람 중 늦참, 일퇴자를 우선하고 나머지를 채우는 방식
        participants_2_temp = []
        
        # 늦참자 먼저 포함 (매칭2에서는 늦게 왔으니 다른 매칭에 못 뛰었을 확률이 높음)
        late_participants = [p for p in members_data if p.get('매칭2_참여') and p.get('늦참')]
        participants_2_temp.extend(late_participants)

        # 매칭1에 참여하지 않은 사람들을 우선 포함 (매칭2로 넘어왔을 가능성)
        match1_ids = {p['이름'] for p in participants_1}
        not_in_match1 = [p for p in members_data if p.get('매칭2_참여') and p['이름'] not in match1_ids and p not in participants_2_temp]
        participants_2_temp.extend(not_in_match1)

        # 일퇴자를 그 다음으로 포함 (매칭2 뛰고 일찍 갈 수 있음)
        early_leave_participants = [p for p in members_data if p.get('매칭2_참여') and p.get('일퇴') and p not in participants_2_temp]
        participants_2_temp.extend(early_leave_participants)

        # 12명이 안되면 나머지 매칭2 참여자 중 랜덤하게 채움
        remaining_needed = 12 - len(participants_2_temp)
        if remaining_needed > 0:
            all_match2_participants = [p for p in members_data if p.get('매칭2_참여')]
            already_selected_ids = {p['이름'] for p in participants_2_temp}
            fill_candidates = [p for p in all_match2_participants if p['이름'] not in already_selected_ids]
            random.shuffle(fill_candidates)
            participants_2_temp.extend(fill_candidates[:remaining_needed])
        
        participants_2 = sorted(participants_2_temp[:12], key=lambda x: x['순위'])


        # --- 매칭 3 참여자 선정 로직 ---
        # 매칭3은 매칭1, 매칭2에서 빠진 사람 중 일퇴, 늦참을 우선하고 나머지를 채우는 방식
        participants_3_temp = []

        # 일퇴자 먼저 포함 (마지막 매칭이라 일퇴자들이 우선적으로 뛰기 좋음)
        early_leave_participants_3 = [p for p in members_data if p.get('매칭3_참여') and p.get('일퇴')]
        participants_3_temp.extend(early_leave_participants_3)

        # 늦참자 다음으로 포함 (늦게 왔으니 마지막 매칭이라도 뛰게 함)
        late_participants_3 = [p for p in members_data if p.get('매칭3_참여') and p.get('늦참') and p not in participants_3_temp]
        participants_3_temp.extend(late_participants_3)

        # 매칭1과 매칭2에 참여하지 않은 사람들을 우선 포함
        match1_ids = {p['이름'] for p in participants_1}
        match2_ids = {p['이름'] for p in participants_2}
        not_in_match1_and_2 = [p for p in members_data if p.get('매칭3_참여') and p['이름'] not in match1_ids and p['이름'] not in match2_ids and p not in participants_3_temp]
        participants_3_temp.extend(not_in_match1_and_2)
        
        # 12명이 안되면 나머지 매칭3 참여자 중 랜덤하게 채움
        remaining_needed_3 = 12 - len(participants_3_temp)
        if remaining_needed_3 > 0:
            all_match3_participants = [p for p in members_data if p.get('매칭3_참여')]
            already_selected_ids_3 = {p['이름'] for p in participants_3_temp}
            fill_candidates_3 = [p for p in all_match3_participants if p['이름'] not in already_selected_ids_3]
            random.shuffle(fill_candidates_3)
            participants_3_temp.extend(fill_candidates_3[:remaining_needed_3])

        participants_3 = sorted(participants_3_temp[:12], key=lambda x: x['순위'])

        # --- 각 매칭별 인원 요약 및 대진표 생성 ---
        def count_gender(participants):
            total = len(participants)
            male = sum(1 for p in participants if p.get('성별') == '남')
            female = sum(1 for p in participants if p.get('성별') == '여')
            return {'total': total, 'male': male, 'female': female}

        summary_1 = count_gender(participants_1)
        summary_2 = count_gender(participants_2)
        summary_3 = count_gender(participants_3)

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

        return render_template(
            'members.html',
            members=members_data, # 전체 멤버 데이터
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
    else:
        # GET 요청 시 초기 화면 (참여자 목록과 체크박스)
        if not members_data: # members_data가 비어있으면 파일 업로드 페이지로 리다이렉트
            return redirect(url_for('index'))
        return render_template('members.html', members=members_data)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
