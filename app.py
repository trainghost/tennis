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

members_data = [] # Global list to store member data


# Map for gender based on name
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
        
        return redirect(url_for('members')) # 파일 업로드 후에도 PRG 패턴 적용
    return "파일 업로드 실패!"


@app.route('/members', methods=['GET', 'POST'])
def members():
    global members_data

    # Initialize match results variables (for GET request or when not calculated yet)
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

    # Process POST request: Update member info and generate match results
    if request.method == 'POST':
        print("--- POST 요청 수신됨 ---")
        # print(f"request.form 데이터: {request.form}") # 디버깅용, 실제 서비스에서는 보안상 주의

        # Update members_data based on form submission
        # Iterate over the original members_data to update it
        for idx, member in enumerate(members_data):
            # Checkbox values
            participate_key = f'participate_{member["이름"]}'
            # '일퇴'와 '늦참' 체크박스는 loop.index0 (즉, idx)로 name이 생성됨
            early_key = f'early_{idx}'
            late_key = f'late_{idx}'

            member['참여'] = participate_key in request.form
            member['일퇴'] = early_key in request.form
            member['늦참'] = late_key in request.form

            # Rank value
            # CRITICAL CHANGE: Get rank directly using the name attribute from HTML
            rank_key = f'rank_{member["이름"]}'
            received_rank = request.form.get(rank_key)
            if received_rank is not None and received_rank.isdigit(): # Ensure it's a digit
                member['순위'] = int(received_rank)
            else:
                # Fallback to current rank if input is empty or invalid
                print(f"경고: {member['이름']}의 순위가 유효하지 않습니다: '{received_rank}'. 이전 순위 ({member['순위']})를 유지합니다.")

        print("--- members_data 업데이트 완료 ---")

        # --- All participants for matching are those with '참여' checked ---
        all_selected_participants = [p for p in members_data if p.get('참여')]
        all_selected_participants_sorted = sorted(all_selected_participants, key=lambda x: x['순위'])
        random_candidates = list(all_selected_participants) # 원본 리스트 복사하여 셔플
        random.shuffle(random_candidates)

        # --- Matching Logic (as previously defined) ---

        # Helper function to create matches for 12 participants
        def create_matches(participants):
            if len(participants) != 12:
                return []

            female_players = sorted([p for p in participants if p['성별'] == '여'], key=lambda x: x['순위'])
            male_players = sorted([p for p in participants if p['성별'] == '남'], key=lambda x: x['순위'])

            matches = []
            
            # Assuming 6 males and 6 females for 3 mixed doubles matches
            # Or other combinations as per your matching logic
            
            # Example for 3 mixed doubles (adjust based on your actual matching rules)
            # This is a simplified example. Your complex matching logic would go here.
            
            # For 3 mixed doubles (3 female, 3 male on each side, total 6 female, 6 male)
            # This logic assumes you have exactly 6 male and 6 female for a clean 3 mixed doubles setup.
            # If not, you need to adjust your matching algorithm.

            # Simplified pairing for demonstration. You would replace this with your actual sophisticated logic.
            # For 12 players, it typically means 3 courts (4 players/court).
            # If it's 3 mixed doubles, you need 6 females and 6 males.
            # If it's mixed with some male-male or female-female, the logic changes.
            
            # For now, let's assume a generic pairing for 12 participants into 3 courts (4 players each)
            # This is a placeholder; you need to insert your specific advanced matching logic here.
            # Example: Pair top female with bottom male, etc.
            
            # Simple example: just divide into 3 courts if exactly 12 players
            court_names = ['코트 3', '코트 4', '코트 5']
            
            # For a more robust solution, you'd apply your precise algorithm (e.g., skill-based pairing)
            # For now, if exactly 12, distribute.
            
            # A very basic distribution if you just need to fill courts, not ideal for skill-based
            shuffled_players = list(participants)
            random.shuffle(shuffled_players) # Shuffle to make pairs random for this generic example

            # Distribute 12 players into 3 courts, 4 players per court
            for i in range(3):
                if len(shuffled_players) >= 4:
                    court_players = shuffled_players[:4]
                    shuffled_players = shuffled_players[4:]
                    
                    # Assuming for now it's just 2 vs 2, or some other setup.
                    # This part needs your specific pairing logic for Team A vs Team B.
                    # For a generic 4-player court, just show them as a group for now.
                    # You will need to implement specific team_a and team_b selection within each court.
                    
                    # For the purpose of getting your UI to show something:
                    # If you strictly want Team A and Team B, you need to pair them.
                    # For example, first two players in court_players are team_a, last two are team_b.
                    if len(court_players) == 4:
                        matches.append({
                            'court': court_names[i],
                            'team_a': [court_players[0], court_players[1]],
                            'team_b': [court_players[2], court_players[3]]
                        })
                    else:
                        print(f"경고: {court_names[i]}에 4명이 배정되지 않았습니다. 현재 {len(court_players)}명.")

            return matches


        # Match 1 Generation
        temp_participants_1 = []
        temp_participants_1_set = set()

        # 1. 일퇴인데 늦참 아닌 사람 우선 (최대한 12명 채우기)
        for p in all_selected_participants_sorted:
            if p.get('일퇴') and not p.get('늦참') and id(p) not in temp_participants_1_set and len(temp_participants_1) < 12:
                temp_participants_1.append(p)
                temp_participants_1_set.add(id(p))

        # 2. 나머지 인원을 순위 높은 순으로 채우기 (일퇴/늦참 조건 없는 사람)
        for p in all_selected_participants_sorted:
            if id(p) not in temp_participants_1_set and len(temp_participants_1) < 12:
                temp_participants_1.append(p)
                temp_participants_1_set.add(id(p))
        
        participants_1 = sorted(temp_participants_1, key=lambda x: x['순위'])[:12]
        p1_ids = {id(p) for p in participants_1}
        non_selected_participants_1 = sorted([p for p in all_selected_participants if id(p) not in p1_ids], key=lambda x: x['순위'])
        team_match_results_1 = create_matches(participants_1)
        summary_1 = count_gender(participants_1)


        # Match 2 Generation
        temp_participants_2 = []
        temp_participants_2_set = set()

        # 1. 일퇴, 늦참 모두 포함된 사람 우선
        for p in all_selected_participants_sorted:
            if (p.get('일퇴') or p.get('늦참')) and id(p) not in temp_participants_2_set and len(temp_participants_2) < 12:
                temp_participants_2.append(p)
                temp_participants_2_set.add(id(p))
        
        # 2. 매칭 1에 없던 사람 우선 (남은 자리 채우기)
        for p in all_selected_participants_sorted:
            if id(p) not in p1_ids and id(p) not in temp_participants_2_set and len(temp_participants_2) < 12:
                temp_participants_2.append(p)
                temp_participants_2_set.add(id(p))

        # 3. 남은 인원 중에서 채우기
        for p in all_selected_participants_sorted:
            if id(p) not in temp_participants_2_set and len(temp_participants_2) < 12:
                temp_participants_2.append(p)
                temp_participants_2_set.add(id(p))
        
        participants_2 = sorted(temp_participants_2, key=lambda x: x['순위'])[:12]
        p2_ids = {id(p) for p in participants_2}
        non_selected_participants_2 = sorted([p for p in all_selected_participants if id(p) not in p2_ids], key=lambda x: x['순위'])
        team_match_results_2 = create_matches(participants_2)
        summary_2 = count_gender(participants_2)


        # Match 3 Generation (Similar logic, potentially different prioritization)
        temp_participants_3 = []
        temp_participants_3_set = set()

        # 1. 일퇴, 늦참 모두 포함된 사람 우선 (M1, M2와 최대한 다르게)
        for p in all_selected_participants_sorted:
            if (p.get('일퇴') or p.get('늦참')) and id(p) not in p1_ids and id(p) not in p2_ids and id(p) not in temp_participants_3_set and len(temp_participants_3) < 12:
                temp_participants_3.append(p)
                temp_participants_3_set.add(id(p))
        
        # 2. 매칭 1, 2에 모두 없던 사람 우선
        for p in all_selected_participants_sorted:
            if id(p) not in p1_ids and id(p) not in p2_ids and id(p) not in temp_participants_3_set and len(temp_participants_3) < 12:
                temp_participants_3.append(p)
                temp_participants_3_set.add(id(p))
        
        # 3. 남은 인원 중에서 채우기
        for p in all_selected_participants_sorted:
            if id(p) not in temp_participants_3_set and len(temp_participants_3) < 12:
                temp_participants_3.append(p)
                temp_participants_3_set.add(id(p))

        participants_3 = sorted(temp_participants_3, key=lambda x: x['순위'])[:12]
        p3_ids = {id(p) for p in participants_3}
        non_selected_participants_3 = sorted([p for p in all_selected_participants if id(p) not in p3_ids], key=lambda x: x['순위'])
        team_match_results_3 = create_matches(participants_3)
        summary_3 = count_gender(participants_3)


        # Store results in session
        session['last_match_results'] = {
            'members_data': members_data, # Updated members_data
            'team_match_results_1': team_match_results_1,
            'summary_1': summary_1,
            'non_selected_participants_1': non_selected_participants_1,
            'team_match_results_2': team_match_results_2,
            'summary_2': summary_2,
            'non_selected_participants_2': non_selected_participants_2,
            'team_match_results_3': team_match_results_3,
            'summary_3': summary_3,
            'non_selected_participants_3': non_selected_participants_3
        }

        return redirect(url_for('members')) # PRG Pattern: Redirect after POST

    # Process GET request: Load stored results or display initial state
    else:
        if 'last_match_results' in session:
            last_results = session['last_match_results']
            members_data = last_results.get('members_data', []) # Load updated members data
            team_match_results_1 = last_results.get('team_match_results_1', [])
            summary_1 = last_results.get('summary_1', {'total': 0, 'male': 0, 'female': 0})
            non_selected_participants_1 = last_results.get('non_selected_participants_1', [])
            team_match_results_2 = last_results.get('team_match_results_2', [])
            summary_2 = last_results.get('summary_2', {'total': 0, 'male': 0, 'female': 0})
            non_selected_participants_2 = last_results.get('non_selected_participants_2', [])
            team_match_results_3 = last_results.get('team_match_results_3', [])
            summary_3 = last_results.get('summary_3', {'total': 0, 'male': 0, 'female': 0})
            non_selected_participants_3 = last_results.get('non_selected_participants_3', [])
        # else: members_data will be empty initially until file is uploaded and processed

    return render_template(
        'members.html',
        members=members_data,
        team_match_results_1=team_match_results_1,
        summary_1=summary_1,
        non_selected_participants_1=non_selected_participants_1,
        team_match_results_2=team_match_results_2,
        summary_2=summary_2,
        non_selected_participants_2=non_selected_participants_2,
        team_match_results_3=team_match_results_3,
        summary_3=summary_3,
        non_selected_participants_3=non_selected_participants_3
    )

if __name__ == '__main__':
    app.run(debug=True)
