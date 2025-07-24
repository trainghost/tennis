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
    '독고혁': '남', '이성훈': '남', '이종욱': '남', '테스': '남', '오리': '여', '김보경': '여', '최하나': '여'
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
                extracted_data.append({
                    '순위': rank,
                    '이름': name,
                    '성별': gender,
                    '참여': False, # 단일 '참여' 체크박스
                    '일퇴': False,
                    '늦참': False
                })

        global members_data
        members_data = extracted_data
        
        return redirect(url_for('members'))
    return "파일 업로드 실패!"


@app.route('/members', methods=['GET', 'POST'])
def members():
    global members_data

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
    
    # 선발되지 않은 참여자 명단 초기화
    non_selected_participants_1 = []
    non_selected_participants_2 = []
    non_selected_participants_3 = []


    if request.method == 'POST':
        print("--- POST 요청 수신됨 ---")
        print(f"request.form 데이터: {request.form}")

        for idx, member in enumerate(members_data):
            participate_key = f'participate_{member["이름"]}' # 단일 참여 체크박스
            rank_key = f'rank_{member["이름"]}'
            early_key = f'early_{idx}'
            late_key = f'late_{idx}'

            member['참여'] = participate_key in request.form
            
            # 순위 업데이트
            received_rank = request.form.get(rank_key)
            member['순위'] = int(received_rank) if received_rank is not None else member['순위']

            # 일퇴/늦참 업데이트
            member['일퇴'] = early_key in request.form
            member['늦참'] = late_key in request.form

            # print(f"업데이트된 멤버: {member['이름']}, 참여: {member['참여']}, 순위: {member['순위']}, 일퇴: {member['일퇴']}, 늦참: {member['늦참']}")

        print("--- members_data 업데이트 완료 ---")

    # 모든 매칭 참여자 풀은 '참여' 체크박스에 체크된 인원들
    all_selected_participants = [p for p in members_data if p.get('참여')]
    
    # 순위에 따라 정렬하여 매칭 선발에 사용 (필요 시)
    all_selected_participants_sorted = sorted(all_selected_participants, key=lambda x: x['순위'])
    # 랜덤 선택을 위해 복사본을 만들어 섞음
    random_candidates = list(all_selected_participants) # 원본 members_data의 참조를 유지해야 하므로, shallow copy 후 인스턴스 ID로 비교
    random.shuffle(random_candidates)


    # --- 매칭 1 참여자 선정 로직 ---
    # 1. 일퇴에 체크한 사람 포함 (늦참이 아닌 사람들 중에서)
    m1_priority_list = [p for p in all_selected_participants if p.get('일퇴') and not p.get('늦참')]
    participants_1.extend(m1_priority_list)
    
    # 2. 12명이 안되면 참여 체크한 사람 중에 랜덤으로 추가 (늦참 체크한 사람은 제외)
    m1_fill_candidates = [p for p in random_candidates if not p.get('늦참') and p not in participants_1]
    
    if len(participants_1) < 12:
        needed = 12 - len(participants_1)
        # 이미 추가된 인원 제외 후, 남아있는 후보들에서 랜덤으로 추가
        eligible_for_random = [p for p in m1_fill_candidates if p not in participants_1]
        participants_1.extend(eligible_for_random[:needed]) # 무작위로 섞였으니 앞에서부터 필요한 만큼 추가

    participants_1 = participants_1[:12] # 최종적으로 12명만 유지
    participants_1 = sorted(participants_1, key=lambda x: x['순위']) # 최종적으로 순위 순으로 정렬

    # 매칭 1에 선발되지 않은 참여자 명단
    p1_ids = {id(p) for p in participants_1}
    non_selected_participants_1 = sorted([p for p in all_selected_participants if id(p) not in p1_ids], key=lambda x: x['순위'])


    # --- 매칭 2 참여자 선정 로직 ---
    # 1. 일퇴에 체크한 사람 포함
    m2_early = [p for p in all_selected_participants if p.get('일퇴')]
    participants_2.extend(m2_early)

    # 2. 늦참에 체크한 사람 포함
    m2_late = [p for p in all_selected_participants if p.get('늦참') and p not in participants_2]
    participants_2.extend(m2_late)

    # 3. 참여 체크한 사람 중 매칭 1에 포함되지 않은 사람 포함
    m1_ids_for_m2_check = {id(p) for p in participants_1} # 매칭 1 참여자의 고유 ID 집합
    m2_not_in_m1 = [p for p in all_selected_participants_sorted if id(p) not in m1_ids_for_m2_check and p not in participants_2]
    if len(participants_2) < 12:
        needed = 12 - len(participants_2)
        participants_2.extend(m2_not_in_m1[:needed]) # 순위순으로 채움 (랜덤 대신)

    # 4. 12명이 안되면 참여 체크한 사람 중에 랜덤으로 추가
    if len(participants_2) < 12:
        needed = 12 - len(participants_2)
        eligible_for_random = [p for p in random_candidates if p not in participants_2]
        participants_2.extend(eligible_for_random[:needed])
    
    participants_2 = participants_2[:12] # 최종적으로 12명만 유지
    participants_2 = sorted(participants_2, key=lambda x: x['순위']) # 최종적으로 순위 순으로 정렬

    # 매칭 2에 선발되지 않은 참여자 명단
    p2_ids = {id(p) for p in participants_2}
    non_selected_participants_2 = sorted([p for p in all_selected_participants if id(p) not in p2_ids], key=lambda x: x['순위'])


    # --- 매칭 3 참여자 선정 로직 ---
    # 1. 일퇴에 체크한 사람 포함
    m3_early = [p for p in all_selected_participants if p.get('일퇴')]
    participants_3.extend(m3_early)

    # 2. 늦참에 체크한 사람 포함
    m3_late = [p for p in all_selected_participants if p.get('늦참') and p not in participants_3]
    participants_3.extend(m3_late)

    # 3. 참여 체크한 사람 중 매칭 1 또는 매칭 2에 포함되지 않은 사람 포함 (순위순)
    p1_ids_set = {id(p) for p in participants_1}
    p2_ids_set = {id(p) for p in participants_2}
    
    # '매칭 1에 포함되지 않았거나 OR 매칭 2에 포함되지 않은 사람'
    m3_not_in_m1_or_m2 = [
        p for p in all_selected_participants_sorted
        if (id(p) not in p1_ids_set or id(p) not in p2_ids_set) # 매칭 1에 없거나 OR 매칭 2에 없는 사람
        and p not in participants_3 # 이미 매칭 3에 선발되지 않은 사람
    ]

    if len(participants_3) < 12:
        needed = 12 - len(participants_3)
        participants_3.extend(m3_not_in_m1_or_m2[:needed]) # 순위순으로 채움

    # 4. 12명이 안되면 참여 체크한 사람 중에 랜덤으로 추가
    if len(participants_3) < 12:
        needed = 12 - len(participants_3)
        eligible_for_random = [p for p in random_candidates if p not in participants_3]
        participants_3.extend(eligible_for_random[:needed])

    participants_3 = participants_3[:12] # 최종적으로 12명만 유지
    participants_3 = sorted(participants_3, key=lambda x: x['순위']) # 최종적으로 순위 순으로 정렬

    # 매칭 3에 선발되지 않은 참여자 명단
    p3_ids = {id(p) for p in participants_3}
    non_selected_participants_3 = sorted([p for p in all_selected_participants if id(p) not in p3_ids], key=lambda x: x['순위'])


    # 성별 요약 계산
    def count_gender(participants):
        total = len(participants)
        male = sum(1 for p in participants if p.get('성별') == '남')
        female = sum(1 for p in participants if p.get('성별') == '여')
        return {'total': total, 'male': male, 'female': female}

    summary_1 = count_gender(participants_1)
    summary_2 = count_gender(participants_2)
    summary_3 = count_gender(participants_3)

    # --- 각 매칭에 대한 팀 생성 함수 호출 (기존 대진표 이미지 기반 로직) ---

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
        elif summary_1['female'] == 4 and summary_1['male'] == 8: # 매칭 1 - 여자 4명 로직 변경 (이미지 반영)
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
        elif summary_2['female'] == 4 and summary_2['male'] == 8: # 매칭 2 - 여자 4명 로직 변경 (이미지 반영)
            team_match_results_2 = [
                {'court': '3번 코트', 'team_a': [female_members_2[0], male_members_2[3]], 'team_b': [female_members_2[1], male_members_2[2]]}, # 여자1위, 남자4위 vs 여자2위, 남자3위
                {'court': '4번 코트', 'team_a': [female_members_2[2], male_members_2[1]], 'team_b': [female_members_2[3], male_members_2[0]]}, # 여자3위, 남자2위 vs 여자4위, 남자1위
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
        elif summary_3['female'] == 4 and summary_3['male'] == 8: # 매칭 3 - 여자 4명 로직 변경 (이미지 반영)
            team_match_results_3 = [
                {'court': '3번 코트', 'team_a': [female_members_3[0], male_members_3[7]], 'team_b': [female_members_3[3], male_members_3[4]]}, # 여자1위, 남자8위 vs 여자4위, 남자5위
                {'court': '4번 코트', 'team_a': [female_members_3[1], male_members_3[6]], 'team_b': [female_members_3[2], male_members_3[5]]}, # 여자2위, 남자7위 vs 여자3위, 남자6위
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
                {'court': '5번 코트', 'team_a': [male_members_3[4], male_members_3[9]], 'team_b': [male_members_3[5], male_members_3[6]]}  # 남자5위, 남자10위 vs 남자6위, 남자9위
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


    print(f"최종 participants_1 길이: {len(participants_1)}")
    print(f"최종 participants_2 길이: {len(participants_2)}")
    print(f"최종 participants_3 길이: {len(participants_3)}")
    # print(f"최종 summary_1: {summary_1}")
    # print(f"최종 team_match_results_1: {team_match_results_1}")


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
        team_match_results_3=team_match_results_3,
        non_selected_participants_1=non_selected_participants_1, 
        non_selected_participants_2=non_selected_participants_2, 
        non_selected_participants_3=non_selected_participants_3 
    )


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
