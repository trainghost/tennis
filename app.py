from flask import Flask, render_template, request, redirect, url_for, session
import pandas as pd
import os
import random
import re

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# 세션 사용을 위한 secret_key 설정 (실제 배포 시에는 더 복잡하고 안전한 값으로 변경해야 합니다)
app.secret_key = 'your_super_secret_key_for_session_management_12345'

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
        
        # 파일 업로드 시에는 이전 매칭 결과 초기화 (새로운 멤버 데이터로 시작하므로)
        if 'last_match_results' in session:
            session.pop('last_match_results', None)
        
        return redirect(url_for('members'))
    return "파일 업로드 실패!"


@app.route('/members', methods=['GET', 'POST'])
def members():
    global members_data

    # 매칭 결과 변수들을 초기화 (GET 요청 시 기본값, POST 요청 시 재계산)
    participants_1 = []
    participants_2 = []
    participants_3 = []
    summary_1 = {'total': 0, 'male': 0, 'female': 0}
    summary_2 = {'total': 0, 'male': 0, 'female': 0}
    summary_3 = {'total': 0, 'male': 0, 'female': 0}
    team_match_results_1 = []
    team_match_results_2 = []
    team_match_results_3 = []
    non_selected_participants_1 = []
    non_selected_participants_2 = []
    non_selected_participants_3 = []

    # POST 요청일 때만 회원 정보 업데이트 및 매칭 결과 생성
    if request.method == 'POST':
        print("--- POST 요청 수신됨 ---")
        print(f"request.form 데이터: {request.form}")

        for idx, member in enumerate(members_data):
            participate_key = f'participate_{member["이름"]}'
            rank_key = f'rank_{member["이름"]}'
            early_key = f'early_{idx}'
            late_key = f'late_{idx}'

            member['참여'] = participate_key in request.form
            received_rank = request.form.get(rank_key)
            member['순위'] = int(received_rank) if received_rank is not None else member['순위']
            member['일퇴'] = early_key in request.form
            member['늦참'] = late_key in request.form

        print("--- members_data 업데이트 완료 ---")

        # --- 모든 매칭 참여자 풀은 '참여' 체크박스에 체크된 인원들 ---
        all_selected_participants = [p for p in members_data if p.get('참여')]
        all_selected_participants_sorted = sorted(all_selected_participants, key=lambda x: x['순위'])
        random_candidates = list(all_selected_participants)
        random.shuffle(random_candidates)

        # --- 매칭 1 참여자 선정 로직 ---
        participants_1_set = set() # 중복 방지를 위한 set
        m1_priority_list = [p for p in all_selected_participants if p.get('일퇴') and not p.get('늦참')]
        for p in m1_priority_list:
            if id(p) not in participants_1_set:
                participants_1.append(p)
                participants_1_set.add(id(p))
        
        eligible_for_random_m1 = [p for p in random_candidates if not p.get('늦참') and id(p) not in participants_1_set]
        if len(participants_1) < 12:
            needed = 12 - len(participants_1)
            for p in eligible_for_random_m1[:needed]:
                if id(p) not in participants_1_set:
                    participants_1.append(p)
                    participants_1_set.add(id(p))

        participants_1 = participants_1[:12]
        participants_1 = sorted(participants_1, key=lambda x: x['순위'])
        p1_ids = {id(p) for p in participants_1}
        non_selected_participants_1 = sorted([p for p in all_selected_participants if id(p) not in p1_ids], key=lambda x: x['순위'])


        # --- 매칭 2 참여자 선정 로직 ---
        participants_2_set = set()
        m2_early = [p for p in all_selected_participants if p.get('일퇴')]
        for p in m2_early:
            if id(p) not in participants_2_set:
                participants_2.append(p)
                participants_2_set.add(id(p))

        m2_late = [p for p in all_selected_participants if p.get('늦참')]
        for p in m2_late:
            if id(p) not in participants_2_set:
                participants_2.append(p)
                participants_2_set.add(id(p))

        m1_ids_for_m2_check = {id(p) for p in participants_1}
        m2_not_in_m1 = [p for p in all_selected_participants_sorted if id(p) not in m1_ids_for_m2_check]
        
        if len(participants_2) < 12:
            needed = 12 - len(participants_2)
            for p in m2_not_in_m1:
                if id(p) not in participants_2_set and len(participants_2) < 12:
                    participants_2.append(p)
                    participants_2_set.add(id(p))
        
        if len(participants_2) < 12:
            needed = 12 - len(participants_2)
            eligible_for_random = [p for p in random_candidates if id(p) not in participants_2_set]
            for p in eligible_for_random[:needed]:
                if id(p) not in participants_2_set:
                    participants_2.append(p)
                    participants_2_set.add(id(p))
                
        participants_2 = participants_2[:12]
        participants_2 = sorted(participants_2, key=lambda x: x['순위'])
        p2_ids = {id(p) for p in participants_2}
        non_selected_participants_2 = sorted([p for p in all_selected_participants if id(p) not in p2_ids], key=lambda x: x['순위'])


        # --- 매칭 3 참여자 선정 로직 ---
        participants_3_set = set()
        m3_early = [p for p in all_selected_participants if p.get('일퇴')]
        for p in m3_early:
            if id(p) not in participants_3_set:
                participants_3.append(p)
                participants_3_set.add(id(p))

        m3_late = [p for p in all_selected_participants if p.get('늦참')]
        for p in m3_late:
            if id(p) not in participants_3_set:
                participants_3.append(p)
                participants_3_set.add(id(p))

        p1_ids_set = {id(p) for p in participants_1}
        p2_ids_set = {id(p) for p in participants_2}
        
        m3_not_in_m1_or_m2 = [
            p for p in all_selected_participants_sorted
            if (id(p) not in p1_ids_set or id(p) not in p2_ids_set)
        ]

        if len(participants_3) < 12:
            needed = 12 - len(participants_3)
            for p in m3_not_in_m1_or_m2:
                if id(p) not in participants_3_set and len(participants_3) < 12:
                    participants_3.append(p)
                    participants_3_set.add(id(p))

        if len(participants_3) < 12:
            needed = 12 - len(participants_3)
            eligible_for_random = [p for p in random_candidates if id(p) not in participants_3_set]
            for p in eligible_for_random[:needed]:
                if id(p) not in participants_3_set:
                    participants_3.append(p)
                    participants_3_set.add(id(p))

        participants_3 = participants_3[:12]
        participants_3 = sorted(participants_3, key=lambda x: x['순위'])
        p3_ids = {id(p) for p in participants_3}
        non_selected_participants_3 = sorted([p for p in all_selected_participants if id(p) not in p3_ids], key=lambda x: x['순위'])


        # 성별 요약 계산 (POST 요청 시에만 계산)
        def count_gender(participants):
            total = len(participants)
            male = sum(1 for p in participants if p.get('성별') == '남')
            female = sum(1 for p in participants if p.get('성별') == '여')
            return {'total': total, 'male': male, 'female': female}

        summary_1 = count_gender(participants_1)
        summary_2 = count_gender(participants_2)
        summary_3 = count_gender(participants_3)

        # --- 각 매칭에 대한 팀 생성 함수 호출 (POST 요청 시에만 계산) ---
        # 매칭 1 대진표
        if summary_1['total'] == 12:
            female_members_1 = sorted([p for p in participants_1 if p['성별'] == '여'], key=lambda x: x['순위'])
            male_members_1 = sorted([p for p in participants_1 if p['성별'] == '남'], key=lambda x: x['순위'])
            if summary_1['female'] == 6 and summary_1['male'] == 6:
                team_match_results_1 = [
                    {'court': '3번 코트', 'team_a': [female_members_1[0], female_members_1[3]], 'team_b': [female_members_1[1], female_members_1[2]]}, # 여1, 여4 vs 여2, 여3
                    {'court': '4번 코트', 'team_a': [female_members_1[4], male_members_1[5]], 'team_b': [female_members_1[5], male_members_1[4]]}, # 여5, 남6 vs 여6, 남5
                    {'court': '5번 코트', 'team_a': [male_members_1[0], male_members_1[3]], 'team_b': [male_members_1[1], male_members_1[2]]}  # 남1, 남4 vs 남2, 남3
                ]
            elif summary_1['female'] == 5 and summary_1['male'] == 7:
                team_match_results_1 = [
                    {'court': '3번 코트', 'team_a': [female_members_1[1], female_members_1[4]], 'team_b': [female_members_1[2], female_members_1[3]]}, # 여자2위, 여자5위 vs 여자3위, 여자4위
                    {'court': '4번 코트', 'team_a': [female_members_1[0], male_members_1[0]], 'team_b': [male_members_1[5], male_members_1[6]]}, # 여자1위, 남자1위 vs 남자6위, 남자7위
                    {'court': '5번 코트', 'team_a': [male_members_1[1], male_members_1[4]], 'team_b': [male_members_1[2], male_members_1[3]]}  # 남자2위, 남자5위 vs 남자3위, 남자4위
                ]
            elif summary_1['female'] == 4 and summary_1['male'] == 8: # 매칭 1 - 여자 4명 로직 (이미지 반영)
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
                    {'court': '3번 코트', 'team_a': [female_members_1[0], male_members_1[1]], 'team_b': [female_members_1[1], male_members_1[0]]}, # 여자1위, 남자2위 vs 여자2위, 남자1위
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
            else:
                team_match_results_1 = []

        # 매칭 2 대진표
        if summary_2['total'] == 12:
            female_members_2 = sorted([p for p in participants_2 if p['성별'] == '여'], key=lambda x: x['순위'])
            male_members_2 = sorted([p for p in participants_2 if p['성별'] == '남'], key=lambda x: x['순위'])
            if summary_2['female'] == 6 and summary_2['male'] == 6:
                team_match_results_2 = [
                    {'court': '3번 코트', 'team_a': [female_members_2[0], female_members_2[5]], 'team_b': [female_members_2[1], female_members_2[4]]}, # 여1, 여6 vs 여2, 여5
                    {'court': '4번 코트', 'team_a': [female_members_2[2], male_members_2[3]], 'team_b': [female_members_2[3], male_members_2[2]]}, # 여3, 남4 vs 여4, 남3
                    {'court': '5번 코트', 'team_a': [male_members_2[0], male_members_2[5]], 'team_b': [male_members_2[1], male_members_2[4]]}  # 남1, 남6 vs 남2, 남5
                ]
            elif summary_2['female'] == 5 and summary_2['male'] == 7:
                team_match_results_2 = [
                    {'court': '3번 코트', 'team_a': [female_members_2[0], male_members_2[0]], 'team_b': [female_members_2[1], male_members_2[1]]}, # 여자1위, 남자1위 vs 여자2위, 남자2위
                    {'court': '4번 코트', 'team_a': [female_members_2[2], male_members_2[2]], 'team_b': [female_members_2[3], male_members_2[3]]}, # 여자3위, 남자3위 vs 여자4위, 남자4위
                    {'court': '5번 코트', 'team_a': [female_members_2[4], male_members_2[4]], 'team_b': [male_members_2[5], male_members_2[6]]}  # 여자5위, 남자5위 vs 남자6위, 남자7위
                ]
            elif summary_2['female'] == 4 and summary_2['male'] == 8: # 매칭 2 - 여자 4명 로직 (이미지 반영)
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
            else:
                team_match_results_2 = []

        # 매칭 3 대진표
        if summary_3['total'] == 12:
            female_members_3 = sorted([p for p in participants_3 if p['성별'] == '여'], key=lambda x: x['순위'])
            male_members_3 = sorted([p for p in participants_3 if p['성별'] == '남'], key=lambda x: x['순위'])
            if summary_3['female'] == 6 and summary_3['male'] == 6:
                team_match_results_3 = [
                    {'court': '3번 코트', 'team_a': [female_members_3[2], female_members_3[5]], 'team_b': [female_members_3[3], female_members_3[4]]}, # 여3, 여6 vs 여4, 여5
                    {'court': '4번 코트', 'team_a': [female_members_3[0], male_members_3[1]], 'team_b': [female_members_3[1], male_members_3[0]]}, # 여1, 남2 vs 여2, 남1
                    {'court': '5번 코트', 'team_a': [male_members_3[2], male_members_3[5]], 'team_b': [male_members_3[3], male_members_3[4]]}  # 남3, 남6 vs 남4, 남5
                ]
            elif summary_3['female'] == 5 and summary_3['male'] == 7:
                team_match_results_3 = [
                    {'court': '3번 코트', 'team_a': [male_members_3[1], female_members_3[3]], 'team_b': [male_members_3[3], female_members_3[0]]}, # 남자2위, 여자4위 vs 남자4위, 여자1위
                    {'court': '4번 코트', 'team_a': [male_members_3[0], female_members_3[4]], 'team_b': [male_members_3[6], female_members_3[2]]}, # 남자1위, 여자5위 vs 남자7위, 여자3위
                    {'court': '5번 코트', 'team_a': [female_members_3[1], male_members_3[2]], 'team_b': [male_members_3[4], male_members_3[5]]}  # 여자2위, 남자3위 vs 남자5위, 남자6위
                ]
            elif summary_3['female'] == 4 and summary_3['male'] == 8: # 매칭 3 - 여자 4명 로직 (이미지 반영)
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
            else:
                team_match_results_3 = []

        # 매칭 결과를 세션에 저장 (페이지 새로고침 시에도 유지되도록)
        session['last_match_results'] = {
            'participants_1': participants_1,
            'participants_2': participants_2,
            'participants_3': participants_3,
            'summary_1': summary_1,
            'summary_2': summary_2,
            'summary_3': summary_3,
            'team_match_results_1': team_match_results_1,
            'team_match_results_2': team_match_results_2,
            'team_match_results_3': team_match_results_3,
            'non_selected_participants_1': non_selected_participants_1,
            'non_selected_participants_2': non_selected_participants_2,
            'non_selected_participants_3': non_selected_participants_3
        }
    else: # GET 요청일 경우, 세션에서 이전 매칭 결과를 불러옴
        if 'last_match_results' in session:
            last_results = session['last_match_results']
            participants_1 = last_results['participants_1']
            participants_2 = last_results['participants_2']
            participants_3 = last_results['participants_3']
            summary_1 = last_results['summary_1']
            summary_2 = last_results['summary_2']
            summary_3 = last_results['summary_3']
            team_match_results_1 = last_results['team_match_results_1']
            team_match_results_2 = last_results['team_match_results_2']
            team_match_results_3 = last_results['team_match_results_3']
            non_selected_participants_1 = last_results['non_selected_participants_1']
            non_selected_participants_2 = last_results['non_selected_participants_2']
            non_selected_participants_3 = last_results['non_selected_participants_3']

    print(f"최종 participants_1 길이: {len(participants_1)}")
    print(f"최종 participants_2 길이: {len(participants_2)}")
    print(f"최종 participants_3 길이: {len(participants_3)}")

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
