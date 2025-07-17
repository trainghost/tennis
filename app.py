from flask import Flask, render_template, request, redirect, url_for
import pandas as pd
import os
import json

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route('/')
def home():
    return render_template('index.html')  # index.html은 기본 페이지로 수정할 수 있음


members_data = []  # 업로드 후 저장

# 매칭 1과 매칭 2 참가자 필터링을 위한 함수
def match_participants(valid_members, early_bird_members):
    # 매칭 1에 포함되지 않은 사람들만 필터링
    not_in_early_bird = [m for m in valid_members if m not in early_bird_members]

    # 매칭 2: 매칭 1에 포함되지 않은 사람들을 우선적으로 추가
    matching_2_candidates = not_in_early_bird[:12]

    # 매칭 2에 12명이 안 채워졌으면, 일퇴와 늦참 체크된 사람들을 포함시킨다
    remaining_count = 12 - len(matching_2_candidates)
    if remaining_count > 0:
        # 일퇴나 늦참을 체크한 사람들 중에서 참여 체크한 사람 추가
        late_and_early_participants = [
            m for m in not_in_early_bird
            if (m.get('일퇴') or m.get('늦참')) and m.get('참가') and m not in matching_2_candidates
        ][:remaining_count]
        matching_2_candidates.extend(late_and_early_participants)

    # 그래도 12명이 안 채워졌다면, 나머지 참여 체크한 사람들 추가
    remaining_count_2 = 12 - len(matching_2_candidates)
    if remaining_count_2 > 0:
        remaining_participants = [
            m for m in not_in_early_bird if m.get('참가') and m not in matching_2_candidates
        ][:remaining_count_2]
        matching_2_candidates.extend(remaining_participants)

    return matching_2_candidates

@app.route('/members', methods=['GET', 'POST'])
def members():
    global members_data  # 이 줄을 함수의 처음에 배치해야 합니다.

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

    # 매칭 2에 대한 처리
    selected_for_matching_2 = match_participants(valid_members, early_bird_members)

    # 매칭 1과 매칭 2 출력 (디버깅용)
    print("매칭 1:", early_bird_members)
    print("매칭 2:", selected_for_matching_2)

    return render_template('members.html', members=members_data, participants_1=early_bird_members, participants_2=selected_for_matching_2)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
