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

@app.route('/upload', methods=['POST'])
def upload():
    file = request.files['file']
    filepath = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(filepath)

    df = pd.read_excel(filepath)
    df['이름'] = df['이름'].astype(str).str.replace(r'^\d+\.\s*', '', regex=True)
    df['순위'] = range(1, len(df) + 1)

    global members_data
    members_data = df.to_dict(orient='records')

    return redirect(url_for('members'))

@app.route('/members', methods=['GET', 'POST'])
def members():
    global members_data

    if request.method == 'POST':
        for idx, member in enumerate(members_data):
            member['참가'] = f'participate_{idx}' in request.form
            member['일퇴'] = f'early_{idx}' in request.form
            member['늦참'] = f'late_{idx}' in request.form

        # 참가자 추출
        part_all = [m for m in members_data if m.get('참가')]

        # === 매칭 1 ===
        m1_early = [m for m in part_all if m.get('일퇴')]
        m1_fill = [m for m in part_all if not m.get('늦참') and m not in m1_early]
        random.shuffle(m1_fill)
        participants_1 = (m1_early + m1_fill)[:12]

        # === 매칭 2 ===
        p2_set = []
        part_late = [m for m in part_all if m.get('늦참')]
        p2_set.extend(part_late)

        m1_ids = set(id(m) for m in participants_1)
        missing_in_m1 = [m for m in part_all if id(m) not in m1_ids]
        for m in missing_in_m1:
            if m not in p2_set:
                p2_set.append(m)

        part_early = [m for m in part_all if m.get('일퇴')]
        for m in part_early:
            if m not in p2_set:
                p2_set.append(m)

        needed = 12 - len(p2_set)
        if needed > 0:
            remaining = [m for m in part_all if m not in p2_set]
            random.shuffle(remaining)
            p2_set.extend(remaining[:needed])

        participants_2 = p2_set[:12]

        # === 매칭 3 ===
        p3_set = []
        part_early = [m for m in part_all if m.get('일퇴')]
        part_late = [m for m in part_all if m.get('늦참')]
        p3_set.extend(part_early)

        for m in part_late:
            if m not in p3_set:
                p3_set.append(m)

        p2_ids = set(id(m) for m in participants_2)
        not_in_p2 = [m for m in part_all if id(m) not in p2_ids]
        for m in not_in_p2:
            if m not in p3_set:
                p3_set.append(m)

        needed = 12 - len(p3_set)
        if needed > 0:
            remaining = [m for m in part_all if m not in p3_set]
            random.shuffle(remaining)
            p3_set.extend(remaining[:needed])

        participants_3 = p3_set[:12]

        return render_template(
            'members.html',
            members=members_data,
            participants_1=participants_1,
            participants_2=participants_2,
            participants_3=participants_3
        )

    return render_template(
        'members.html',
        members=members_data,
        participants_1=[],
        participants_2=[],
        participants_3=[]
    )

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
