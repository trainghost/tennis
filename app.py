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
    
    # 선발되지 않은 참여자 명단 초기화 (이제 all_matched_ids로 통합 관리)
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

        print("--- members_data 업데이트 완료 ---")

    # 모든 매칭 참여자 풀은 '참여' 체크박스에 체크된 인원들
    all_selected_participants = [p for p in members_data if p.get('참여')]
    
    # 랜덤 선택을 위해 복사본을 만들어 섞음 (원본 리스트에 영향 주지 않도록)
    random_candidates = list(all_selected_participants) 
    random.shuffle(random_candidates)

    # 모든 매칭에서 선발된 인원들의 ID를 추적하기 위한 집합
    # 이 집합은 각 매칭 선발 시 후보군에서 이미 뽑힌 사람을 제외하는 데 사용됩니다.
    all_matched_ids = set()

    # 각 매칭별 여성 4명 선발 로직을 함수로 분리 (재사용성을 위해)
    # 이 함수는 이제 all_matched_ids를 인자로 받아 이미 뽑힌 사람을 제외하고 여성 4명을 뽑습니다.
    def select_four_females(all_female_participants, current_matched_ids):
        selected_females = []
        
        # 1. 일퇴에 체크한 여성 우선 선발 (아직 어떤 매칭에서도 선택되지 않은 여성 중에서)
        early_females = [p for p in all_female_participants if p.get('일퇴') and id(p) not in current_matched_ids]
        random.shuffle(early_females)

        for f in early_females:
            if len(selected_females) < 4:
                selected_females.append(f)
            else:
                break
        
        # 2. 4명이 안되면 나머지 여성 중에서 랜덤으로 채움 (아직 어떤 매칭에서도 선택되지 않은 여성 중에서)
        if len(selected_females) < 4:
            needed = 4 - len(selected_females)
            # 현재 selected_females에 포함된 여성과 all_matched_ids에 이미 있는 여성을 제외
            remaining_females = [p for p in all_female_participants if id(p) not in current_matched_ids and p not in selected_females]
            random.shuffle(remaining_females)
            
            selected_females.extend(remaining_females[:needed])
            
        return selected_females

    # 모든 참여 여성 목록
    all_female_participants = [p for p in all_selected_participants if p['성별'] == '여']


    # --- 매칭 1 참여자 선정 로직 ---
    participants_1 = []
    # 1. 여성 4명 선발
    selected_females_1 = select_four_females(all_female_participants, all_matched_ids)
    participants_1.extend(selected_females_1)
    
    # 선발된 여성 ID를 all_matched_ids에 추가
    for p in selected_females_1:
        all_matched_ids.add(id(p))

    # 2. 일퇴에 체크한 남성 우선 선발 (늦참이 아닌 사람들 중에서, 이미 선택되지 않은 인원 중)
    m1_early_males = [p for p in all_selected_participants if p.get('성별') == '남' and p.get('일퇴') and not p.get('늦참') and id(p) not in all_matched_ids]
    random.shuffle(m1_early_males)
    
    for male in m1_early_males:
        if len(participants_1) < 12: 
            participants_1.append(male)
            all_matched_ids.add(id(male)) # 전체 매칭 ID 집합에 추가
        else:
            break # 12명 채워지면 중단

    # 3. 12명이 안되면 참여 체크한 사람 중에 랜덤으로 추가 (늦참 체크한 사람은 제외, 이미 선택되지 않은 인원 중)
    # 현재 participants_1에 있는 인원과 all_matched_ids에 있는 인원 모두 제외
    m1_fill_candidates = [p for p in random_candidates if not p.get('늦참') and id(p) not in all_matched_ids]
    random.shuffle(m1_fill_candidates)
    
    for p in m1_fill_candidates:
        if len(participants_1) < 12:
            participants_1.append(p)
            all_matched_ids.add(id(p)) # 전체 매칭 ID 집합에 추가
        else:
            break

    participants_1 = participants_1[:12] # 최종적으로 12명만 유지 (혹시 모를 초과 방지)
    random.shuffle(participants_1) # 최종 매칭 1 인원도 랜덤으로 섞음


    # --- 매칭 2 참여자 선정 로직 ---
    participants_2 = []
    # 1. 여성 4명 선발 (아직 아무 매칭에도 뽑히지 않은 여성 중에서)
    selected_females_2 = select_four_females(all_female_participants, all_matched_ids)
    participants_2.extend(selected_females_2)

    for p in selected_females_2:
        all_matched_ids.add(id(p))

    # 2. 일퇴에 체크한 남성 우선 선발 (이미 선택되지 않은 인원 중)
    m2_early_males = [p for p in all_selected_participants if p.get('성별') == '남' and p.get('일퇴') and id(p) not in all_matched_ids]
    random.shuffle(m2_early_males)
    for male in m2_early_males:
        if len(participants_2) < 12:
            participants_2.append(male)
            all_matched_ids.add(id(male))
        else:
            break

    # 3. 늦참에 체크한 사람 중 아직 포함되지 않은 사람 포함 (이미 선택되지 않은 인원 중)
    m2_late = [p for p in all_selected_participants if p.get('늦참') and id(p) not in all_matched_ids]
    random.shuffle(m2_late)
    for late_p in m2_late:
        if len(participants_2) < 12:
            participants_2.append(late_p)
            all_matched_ids.add(id(late_p))
        else:
            break

    # 4. 나머지 참여 체크한 사람 중 아직 포함되지 않은 사람 랜덤으로 추가
    m2_fill_candidates = [p for p in random_candidates if id(p) not in all_matched_ids]
    random.shuffle(m2_fill_candidates)
    
    for p in m2_fill_candidates:
        if len(participants_2) < 12:
            participants_2.append(p)
            all_matched_ids.add(id(p))
        else:
            break
    
    participants_2 = participants_2[:12]
    random.shuffle(participants_2) # 최종 매칭 2 인원도 랜덤으로 섞음


    # --- 매칭 3 참여자 선정 로직 ---
    participants_3 = []
    # 1. 여성 4명 선발 (아직 아무 매칭에도 뽑히지 않은 여성 중에서)
    selected_females_3 = select_four_females(all_female_participants, all_matched_ids)
    participants_3.extend(selected_females_3)

    for p in selected_females_3:
        all_matched_ids.add(id(p))

    # 2. 일퇴에 체크한 남성 우선 선발 (이미 선택되지 않은 인원 중)
    m3_early_males = [p for p in all_selected_participants if p.get('성별') == '남' and p.get('일퇴') and id(p) not in all_matched_ids]
    random.shuffle(m3_early_males)
    for male in m3_early_males:
        if len(participants_3) < 12:
            participants_3.append(male)
            all_matched_ids.add(id(male))
        else:
            break

    # 3. 늦참에 체크한 사람 중 아직 포함되지 않은 사람 포함 (이미 선택되지 않은 인원 중)
    m3_late = [p for p in all_selected_participants if p.get('늦참') and id(p) not in all_matched_ids]
    random.shuffle(m3_late)
    for late_p in m3_late:
        if len(participants_3) < 12:
            participants_3.append(late_p)
            all_matched_ids.add(id(late_p))
        else:
            break

    # 4. 나머지 참여 체크한 사람 중 아직 포함되지 않은 사람 랜덤으로 추가
    m3_fill_candidates = [p for p in random_candidates if id(p) not in all_matched_ids]
    random.shuffle(m3_fill_candidates)

    for p in m3_fill_candidates:
        if len(participants_3) < 12:
            participants_3.append(p)
            all_matched_ids.add(id(p))
        else:
            break

    participants_3 = participants_3[:12] 
    random.shuffle(participants_3) # 최종 매칭 3 인원도 랜덤으로 섞음


    # 매칭되지 않은 참여자 명단 업데이트 (all_matched_ids를 기반으로 최종 남은 인원만 계산)
    non_selected_final = sorted([p for p in all_selected_participants if id(p) not in all_matched_ids], key=lambda x: x['순위'])

    # 기존의 매칭별 non_selected_participants에 최종 남은 사람 목록을 할당
    non_selected_participants_1 = non_selected_final
    non_selected_participants_2 = non_selected_final
    non_selected_participants_3 = non_selected_final


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
    # 이 부분은 매칭된 인원들을 기반으로 하므로, 위에서 랜덤으로 섞인 participants_X를 사용합니다.
    # 단, 대진표를 구성할 때는 다시 순위나 특정 기준에 따라 정렬해야 할 수 있습니다.
    # 현재 대진표 로직은 '순위'를 기반으로 하고 있으므로, 이 부분을 랜덤으로 변경하려면
    # 대진표 구성 로직도 랜덤으로 변경해야 합니다.
    # 여기서는 대진표 구성 로직은 변경하지 않고, 선발된 인원 자체만 랜덤으로 섞습니다.

    # 매칭 1 대진표 (오버라이드 로직 포함)
    if summary_1['total'] == 12:
        # 대진표 구성을 위해 다시 순위순으로 정렬 (혹은 대진표 자체를 랜덤으로 구성하는 로직 필요)
        female_members_1 = sorted([p for p in participants_1 if p['성별'] == '여'], key=lambda x: x['순위'])
        male_members_1 = sorted([p       for p in participants_1 if p['성별'] == '남'], key=lambda x: x['순위'])

        if summary_1['female'] == 5 and summary_1['male'] == 7: # 이 조건에 걸리면 그대로 5명으로 대진표를 만듦
            team_match_results_1 = [
                {'court': '3번 코트', 'team_a': [female_members_1[1], female_members_1[4]], 'team_b': [female_members_1[2], female_members_1[3]]}, # 여자2위, 여자5위 vs 여자3위, 여자4위
                {'court': '4번 코트', 'team_a': [female_members_1[0], male_members_1[0]], 'team_b': [male_members_1[5], male_members_1[6]]}, # 여자1위, 남자1위 vs 남자6위, 남자7위
                {'court': '5번 코트', 'team_a': [male_members_1[1], male_members_1[4]], 'team_b': [male_members_1[2], male_members_1[3]]}  # 남자2위, 남자5위 vs 남자3위, 남자4위
            ]
        elif summary_1['female'] == 4 and summary_1['male'] == 8: # 이 조건에 걸리도록 수정된 로직이 목표
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
        else: # 예상치 못한 성별 구성일 경우
            team_match_results_1 = []

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
        else:
            team_match_results_2 = []

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
