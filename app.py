from flask import Flask, render_template, request, redirect, url_for
import pandas as pd
import os
import random
import re

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

members_data = []

# 이름 → 성별 매핑
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
            extracted_data.append({'순위': rank, '이름': name})

    global members_data
    members_data = extracted_data

    return redirect(url_for('members'))

@app.route('/members', methods=['GET', 'POST'])
def members():
    if request.method == 'POST':
        for idx, member in enumerate(members_data):
            member['참가'] = f'participate_{idx}' in request.form
            member['일퇴'] = f'early_{idx}' in request.form
            member['늦참'] = f'late_{idx}' in request.form

        # 매칭 1
        participants_1 = sorted([m for m in members_data if m.get('참가')], key=lambda x: x['순위'])[:12]

        # 여자가 몇 명 있는지 계산
        female_count = sum(1 for p in participants_1 if gender_map.get(p['이름']) == '여')

        # 코트별 대진표 생성
        matches = {
            '3번코트': [],
            '4번코트': [],
            '5번코트': []
        }

        # 여자의 수에 따른 대진표 작성
        if female_count == 0:
            matches['3번코트'] = [(participants_1[0], participants_1[-1]), (participants_1[1], participants_1[-2]), (participants_1[2], participants_1[-3]), (participants_1[3], participants_1[-4])]
            matches['4번코트'] = [(participants_1[4], participants_1[-5]), (participants_1[5], participants_1[-6]), (participants_1[6], participants_1[-7]), (participants_1[7], participants_1[-8])]
            matches['5번코트'] = [(participants_1[8], participants_1[-9]), (participants_1[9], participants_1[-10]), (participants_1[10], participants_1[-11]), (participants_1[11], participants_1[0])]
        
        elif female_count == 1:
            matches['3번코트'] = [(participants_1[0], participants_1[12 - female_count - 1]), (participants_1[1], participants_1[2])]
            matches['4번코트'] = [(participants_1[3], participants_1[-4]), (participants_1[4], participants_1[-5]), (participants_1[5], participants_1[-6]), (participants_1[6], participants_1[-7])]
            matches['5번코트'] = [(participants_1[7], participants_1[-8]), (participants_1[8], participants_1[-9]), (participants_1[9], participants_1[-10]), (participants_1[10], participants_1[-11])]
        
        elif female_count == 2:
            matches['3번코트'] = [(participants_1[0], participants_1[1]), (participants_1[2], participants_1[3])]
            matches['4번코트'] = [(participants_1[4], participants_1[5]), (participants_1[6], participants_1[7])]
            matches['5번코트'] = [(participants_1[8], participants_1[9]), (participants_1[10], participants_1[11])]
        
        elif female_count == 3:
            matches['3번코트'] = [(participants_1[0], participants_1[1]), (participants_1[2], participants_1[3])]
            matches['4번코트'] = [(participants_1[4], participants_1[5]), (participants_1[6], participants_1[7])]
            matches['5번코트'] = [(participants_1[8], participants_1[9]), (participants_1[10], participants_1[11])]

        elif female_count == 4:
            matches['3번코트'] = [(participants_1[0], participants_1[1]), (participants_1[2], participants_1[3])]
            matches['4번코트'] = [(participants_1[4], participants_1[5]), (participants_1[6], participants_1[7])]
            matches['5번코트'] = [(participants_1[8], participants_1[9]), (participants_1[10], participants_1[11])]

        elif female_count == 5:
            matches['3번코트'] = [(participants_1[0], participants_1[1]), (participants_1[2], participants_1[3])]
            matches['4번코트'] = [(participants_1[4], participants_1[5]), (participants_1[6], participants_1[7])]
            matches['5번코트'] = [(participants_1[8], participants_1[9]), (participants_1[10], participants_1[11])]

        return render_template(
            'members.html',
            members=members_data,
            participants_1=participants_1,
            matches=matches  # 대진표 추가
        )

    return render_template(
        'members.html',
        members=members_data,
        participants_1=[],
        matches={}  # 대진표 초기화
    )

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
