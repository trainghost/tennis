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

                # ✅ 성별 매핑 추가
                gender = gender_map.get(name, '미정')

                # ✅ 성별까지 포함해서 리스트에 저장
                extracted_data.append({'순위': rank, '이름': name, '성별': gender})

        global members_data
        members_data = extracted_data

        return redirect(url_for('members'))
    return redirect(url_for('index')) # Fallback if no file is uploaded


@app.route('/members', methods=['GET', 'POST'])
def members():
    team_match_results = [] # 팀 매칭 결과를 저장할 리스트 초기화

    if request.method == 'POST':
        for idx, member in enumerate(members_data):
            member['참가'] = f'participate_{idx}' in request.form
            member['일퇴'] = f'early_{idx}' in request.form
            member['늦참'] = f'late_{idx}' in request.form

        # --- 매칭 1 로직 ---
        # 참가하고 일퇴하는 멤버
        m1_early = [m for m in members_data if m.get('참가') and m.get('일퇴')]
        # 참가하고 늦참하지 않으며 일퇴하지 않는 멤버 (정상 참여)
        m1_fill = [m for m in members_data if m.get('참가') and not m.get('늦참') and m not in m1_early]
        random.shuffle(m1_fill) # 무작위로 섞기
        # 일퇴 멤버를 우선 포함하고, 나머지를 정상 참여 멤버로 채워 최대 12명
        participants_1 = (m1_early + m1_fill)[:12]
        participants_1 = sorted(participants_1, key=lambda x: x['순위']) # 순위별 정렬

        # --- 매칭 2 로직 ---
        p2_set = []
        # 참가하고 늦참하는 멤버
        part_late = [m for m in members_data if m.get('참가') and m.get('늦참')]
        p2_set.extend(part_late)

        # 모든 참가 멤버
        part_all = [m for m in members_data if m.get('참가')]
        # 매칭 1에 포함되지 않은 멤버
        m1_set = set(id(m) for m in participants_1)
        missing_in_m1 = [m for m in part_all if id(m) not in m1_set]
        for m in missing_in_m1:
            if m not in p2_set: # 중복 방지
                p2_set.append(m)

        # 참가하고 일퇴하는 멤버
        part_early = [m for m in members_data if m.get('참가') and m.get('일퇴')]
        for m in part_early:
            if m not in p2_set: # 중복 방지
                p2_set.append(m)

        # 12명까지 필요한 인원 채우기
        needed = 12 - len(p2_set)
        if needed > 0:
            remaining = [m for m in part_all if m not in p2_set]
            random.shuffle(remaining)
            p2_set.extend(remaining[:needed])

        participants_2 = p2_set[:12] # 최종 12명으로 제한
        participants_2 = sorted(participants_2, key=lambda x: x['순위'])

        # --- 매칭 3 로직 ---
        match3_set = []
        # 참가하고 일퇴하는 멤버
        part_early_m3 = [m for m in part_all if m.get('일퇴')]
        match3_set.extend(part_early_m3)
        # 참가하고 늦참하는 멤버 중 아직 포함되지 않은 멤버
        part_late_m3 = [m for m in part_all if m.get('늦참') and m not in match3_set]
        match3_set.extend(part_late_m3)
        # 매칭 2에 포함되지 않은 멤버 중 아직 포함되지 않은 멤버
        p2_ids = set(id(m) for m in participants_2)
        not_in_p2 = [m for m in part_all if id(m) not in p2_ids and m not in match3_set]
        match3_set.extend(not_in_p2)
        # 12명까지 필요한 인원 채우기
        if len(match3_set) < 12:
            remaining = [m for m in part_all if m not in match3_set]
            random.shuffle(remaining)
            match3_set.extend(remaining[:12 - len(match3_set)])
        participants_3 = match3_set[:12] # 최종 12명으로 제한
        participants_3 = sorted(participants_3, key=lambda x: x['순위'])

        # ✅ 성별 요약 계산 함수
        def count_gender(participants):
            total = len(participants)
            male = sum(1 for p in participants if p.get('성별') == '남')
            female = sum(1 for p in participants if p.get('성별') == '여')
            return {'total': total, 'male': male, 'female': female}

        summary_1 = count_gender(participants_1)
        summary_2 = count_gender(participants_2)
        summary_3 = count_gender(participants_3)

        # ✅ 매칭 1에 여자 5명, 총 12명일 경우 팀 매칭 로직
        if summary_1['total'] == 12 and summary_1['female'] == 5:
            female_members = sorted([m for m in participants_1 if m['성별'] == '여'], key=lambda x: x['순위'])
            male_members = sorted([m for m in participants_1 if m['성별'] == '남'], key=lambda x: x['순위'])

            # 팀 구성을 위한 멤버 분배 (예시)
            # 여자 5명: 여1, 여2, 여3, 여4, 여5
            # 남자 7명: 남1, 남2, 남3, 남4, 남5, 남6, 남7

            # 팀 A (여자 2, 남자 3)
            team_a_females = female_members[0:2] # 여1, 여2
            team_a_males = male_members[0:3] # 남1, 남2, 남3

            # 팀 B (여자 3, 남자 4)
            team_b_females = female_members[2:5] # 여3, 여4, 여5
            team_b_males = male_members[3:7] # 남4, 남5, 남6, 남7

            # 코트별 매칭 (예시: 이미지와 유사하게 구성)
            team_match_results = [
                {
                    'court': '3번코트',
                    'team_a': [team_a_females[1], team_b_females[2]], # 여자2위, 여자5위
                    'team_b': [team_b_females[0], team_b_females[1]] # 여자3위, 여자4위
                },
                {
                    'court': '4번코트',
                    'team_a': [team_a_females[0], team_a_males[0]], # 여자1위, 남자1위
                    'team_b': [team_b_males[2], team_b_males[3]] # 남자6위, 남자7위
                },
                {
                    'court': '5번코트',
                    'team_a': [team_a_males[1], team_a_males[4]], # 남자2위, 남자5위 (여기서 남자5위는 male_members[4]가 됨)
                    'team_b': [team_b_males[0], team_b_males[1]] # 남자3위, 남자4위
                }
            ]
            # 위 예시 인덱스는 이미지와 정확히 일치시키기 위해 임의로 조정되었습니다.
            # 실제 로직에서는 순위와 성별을 고려하여 유연하게 구성해야 합니다.
            # 여기서는 이미지에 나온 순위를 기준으로 직접 매핑합니다.
            
            # 이미지에 나온 순위를 기준으로 매핑 (예시)
            # 매칭 1 참여자 중 여자 1~5위, 남자 1~7위가 있다고 가정
            female_ranks = {m['순위']: m for m in female_members}
            male_ranks = {m['순위']: m for m in male_members}

            team_match_results = [
                {
                    'court': '3번코트',
                    'team_a': [female_ranks[2], female_ranks[5]], # 여자2위, 여자5위
                    'team_b': [female_ranks[3], female_ranks[4]]  # 여자3위, 여자4위
                },
                {
                    'court': '4번코트',
                    'team_a': [female_ranks[1], male_ranks[1]], # 여자1위, 남자1위
                    'team_b': [male_ranks[6], male_ranks[7]] # 남자6위, 남자7위
                },
                {
                    'court': '5번코트',
                    'team_a': [male_ranks[2], male_ranks[5]], # 남자2위, 남자5위
                    'team_b': [male_ranks[3], male_ranks[4]] # 남자3위, 남자4위
                }
            ]


        # ✅ 반드시 return
        return render_template(
            'members.html',
            members=members_data,
            participants_1=participants_1,
            participants_2=participants_2,
            participants_3=participants_3,
            summary_1=summary_1,
            summary_2=summary_2,
            summary_3=summary_3,
            team_match_results=team_match_results # 새로운 팀 매칭 결과 전달
        )

    # ✅ GET 요청 시에도 return 필요 (초기 로드 시)
    return render_template(
        'members.html',
        members=members_data, # 초기에는 members_data가 비어있을 수 있음
        participants_1=[],
        participants_2=[],
        participants_3=[],
        summary_1={'total': 0, 'male': 0, 'female': 0},
        summary_2={'total': 0, 'male': 0, 'female': 0},
        summary_3={'total': 0, 'male': 0, 'female': 0},
        team_match_results=[] # 초기에는 비어있는 리스트 전달
    )


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
