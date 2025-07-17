from flask import Flask, render_template, request, redirect, url_for
import pandas as pd
import os
import json

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

members_data = []  # 업로드 후 저장

@app.route('/')
def index():
    return render_template('upload.html')

@app.route('/upload', methods=['POST'])
def upload():
    file = request.files['file']
    filepath = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(filepath)
    df = pd.read_excel(filepath)

    global members_data
    members_data = df.to_dict(orient='records')  # [{'이름': '홍길동', '순위': 1}, ...]
    
    return redirect(url_for('members'))  # 업로드 후 /members로 리다이렉트

@app.route('/members', methods=['GET', 'POST'])
def members():
    global members_data

    if request.method == 'POST':
        updated_data = []
        for i, member in enumerate(members_data):
            # 체크박스 상태 업데이트
            member['참가'] = request.form.get(f'participate_{i}') == 'on'
            member['일퇴'] = request.form.get(f'early_{i}') == 'on'
            member['늦참'] = request.form.get(f'late_{i}') == 'on'
            updated_data.append(member)

        # JSON으로 저장
        with open('members.json', 'w', encoding='utf-8') as f:
            json.dump(updated_data, f, ensure_ascii=False, indent=2)

        members_data = updated_data  # 업데이트된 데이터 반영

        # 리다이렉트: 'GET' 요청으로 페이지 새로 고침
        return redirect(url_for('members'))

    # 조건에 맞는 사람들 필터링
    valid_members = [
        member for member in members_data
        if member.get('참가') and not member.get('늦참')  # 참가자 중에서 늦참 체크된 사람 제외
    ]

    # 매칭 1: 일퇴 체크된 사람 우선적으로 12명 추출
    early_bird_members = [m for m in valid_members if m.get('일퇴')][:12]  # 일퇴 체크된 사람들 먼저 포함

    # 일퇴 체크된 사람이 12명 미만이라면, 나머지 사람들을 추가
    remaining_count = 12 - len(early_bird_members)
    if remaining_count > 0:
        remaining_members = [m for m in valid_members if not m.get('일퇴')][:remaining_count]
        early_bird_members.extend(remaining_members)

    # 매칭 1에 포함되지 않은 사람들 필터링
    not_in_early_bird = [m for m in valid_members if m not in early_bird_members]

    # 매칭 2: 늦참을 우선 포함 (늦참 체크된 사람)
    late_members = [m for m in not_in_early_bird if m.get('늦참')][:12]  # 늦참 체크된 사람들 우선

    # 매칭 2에 늦참이 부족하면 나머지 사람들을 추가 (매칭 1에 포함되지 않은 사람 중에서)
    remaining_count_2 = 12 - len(late_members)
    if remaining_count_2 > 0:
        remaining_members_2 = [m for m in not_in_early_bird if m not in late_members][:remaining_count_2]
        late_members.extend(remaining_members_2)

    # 매칭 2에 일퇴 체크된 사람들 추가
    early_bird_in_matching_2 = [m for m in late_members if m.get('일퇴')][:12]
    remaining_count_3 = 12 - len(early_bird_in_matching_2)
    if remaining_count_3 > 0:
        remaining_members_3 = [m for m in late_members if m not in early_bird_in_matching_2][:remaining_count_3]
        early_bird_in_matching_2.extend(remaining_members_3)

    # 매칭 2에 참여 체크된 사람들 추가 (12명이 안 채워졌다면)
    remaining_count_4 = 12 - len(early_bird_in_matching_2)
    if remaining_count_4 > 0:
        remaining_participants = [m for m in valid_members if m not in late_members and m not in early_bird_in_matching_2][:remaining_count_4]
        early_bird_in_matching_2.extend(remaining_participants)

    # 매칭 1과 매칭 2 출력 (디버깅용)
    print("매칭 1:", early_bird_members)
    print("매칭 2:", early_bird_in_matching_2)

    return render_template('members.html', members=members_data, participants_1=early_bird_members, participants_2=early_bird_in_matching_2)




if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
