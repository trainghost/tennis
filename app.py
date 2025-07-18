from flask import Flask, render_template, request, redirect, url_for
import pandas as pd
import os
import random

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

members_data = []

@app.route('/')
def index():
    return render_template('upload.html')

import re  # 상단에 추가 필요

@app.route('/upload', methods=['POST'])
def upload():
    file = request.files['file']
    filepath = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(filepath)

    # 엑셀의 첫 번째 열만 사용
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

        # 매칭 1: 참가 + 일퇴 우선 → 부족하면 참가+늦참 ❌ 중 랜덤
        m1_early = [m for m in members_data if m.get('참가') and m.get('일퇴')]
        m1_fill = [m for m in members_data if m.get('참가') and not m.get('늦참') and m not in m1_early]
        random.shuffle(m1_fill)
        participants_1 = (m1_early + m1_fill)[:12]

        # 매칭 2: 조건별로 차례로 구성
        p2_set = []

        # 1. 참가 + 늦참 체크한 사람
        part_late = [m for m in members_data if m.get('참가') and m.get('늦참')]
        p2_set.extend(part_late)

        # 2. 참가했지만 매칭 1에 빠진 사람
        part_all = [m for m in members_data if m.get('참가')]
        m1_set = set(id(m) for m in participants_1)
        missing_in_m1 = [m for m in part_all if id(m) not in m1_set]
        for m in missing_in_m1:
            if m not in p2_set:
                p2_set.append(m)

        # 3. 참가 + 일퇴 체크한 사람
        part_early = [m for m in members_data if m.get('참가') and m.get('일퇴')]
        for m in part_early:
            if m not in p2_set:
                p2_set.append(m)

        # 4. 부족하면 참가자 중 남은 사람 랜덤 추가
        needed = 12 - len(p2_set)
        if needed > 0:
            remaining = [m for m in part_all if m not in p2_set]
            random.shuffle(remaining)
            p2_set.extend(remaining[:needed])

        participants_2 = p2_set[:12]

        return render_template(
            'members.html',
            members=members_data,
            participants_1=participants_1,
            participants_2=participants_2
        )

    return render_template(
        'members.html',
        members=members_data,
        participants_1=[],
        participants_2=[]
    )

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
