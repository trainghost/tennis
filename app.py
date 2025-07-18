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

            # ✅ 성별 매핑 추가
            gender = gender_map.get(name, '미정')

            # ✅ 성별까지 포함해서 리스트에 저장
            extracted_data.append({'순위': rank, '이름': name, '성별': gender})

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

        # --- 매칭 1 로직 ---
        m1_early = [m for m in members_data if m.get('참가') and m.get('일퇴')]
        m1_fill = [m for m in members_data if m.get('참가') and not m.get('늦참') and m not in m1_early]
        random.shuffle(m1_fill)
        participants_1 = (m1_early + m1_fill)[:12]
        participants_1 = sorted(participants_1, key=lambda x: x['순위'])

        # --- 매칭 2 로직 ---
        p2_set = []
        part_late = [m for m in members_data if m.get('참가') and m.get('늦참')]
        p2_set.extend(part_late)

        part_all = [m for m in members_data if m.get('참가')]
        m1_set = set(id(m) for m in participants_1)
        missing_in_m1 = [m for m in part_all if id(m) not in m1_set]
        for m in missing_in_m1:
            if m not in p2_set:
                p2_set.append(m)

        part_early = [m for m in members_data if m.get('참가') and m.get('일퇴')]
        for m in part_early:
            if m not in p2_set:
                p2_set.append(m)

        needed = 12 - len(p2_set)
        if needed > 0:
            remaining = [m for m in part_all if m not in p2_set]
            random.shuffle(remaining)
            p2_set.extend(remaining[:needed])

        participants_2 = p2_set[:12]
        participants_2 = sorted(participants_2, key=lambda x: x['순위'])

        # --- 매칭 3 로직 ---
        match3_set = []
        part_early = [m for m in part_all if m.get('일퇴')]
        match3_set.extend(part_early)
        part_late = [m for m in part_all if m.get('늦참') and m not in match3_set]
        match3_set.extend(part_late)
        p2_ids = set(id(m) for m in participants_2)
        not_in_p2 = [m for m in part_all if id(m) not in p2_ids and m not in match3_set]
        match3_set.extend(not_in_p2)
        if len(match3_set) < 12:
            remaining = [m for m in part_all if m not in match3_set]
            random.shuffle(remaining)
            match3_set.extend(remaining[:12 - len(match3_set)])
        participants_3 = match3_set[:12]
        participants_3 = sorted(participants_3, key=lambda x: x['순위'])

        # ✅ 성별 요약 계산
        def count_gender(participants):
            total = len(participants)
            male = sum(1 for p in participants if p.get('성별') == '남')
            female = sum(1 for p in participants if p.get('성별') == '여')
            return {'total': total, 'male': male, 'female': female}

        summary_1 = count_gender(participants_1)
        summary_2 = count_gender(participants_2)
        summary_3 = count_gender(participants_3)

        # ✅ 반드시 return
        return render_template(
            'members.html',
            members=members_data,
            participants_1=participants_1,
            participants_2=participants_2,
            participants_3=participants_3,
            summary_1=summary_1,
            summary_2=summary_2,
            summary_3=summary_3
        )

    # ✅ GET 요청 시에도 return 필요
    return render_template(
        'members.html',
        members=members_data,
        participants_1=[],
        participants_2=[],
        participants_3=[],
        summary_1={'total': 0, 'male': 0, 'female': 0},
        summary_2={'total': 0, 'male': 0, 'female': 0},
        summary_3={'total': 0, 'male': 0, 'female': 0}
    )



if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
