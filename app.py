from flask import Flask, render_template, request, redirect, url_for
import pandas as pd
import os
import random

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

members_data = []  # 엑셀에서 업로드된 회원 정보 저장

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
    members_data = df.to_dict(orient='records')

    return redirect(url_for('members'))

@app.route('/members', methods=['GET', 'POST'])
def members():
    if request.method == 'POST':
        for idx, member in enumerate(members_data):
            member['참가'] = f'participate_{idx}' in request.form
            member['일퇴'] = f'early_{idx}' in request.form
            member['늦참'] = f'late_{idx}' in request.form

        # Step 1: 참가 && 일퇴 체크된 사람
        early_participants = [m for m in members_data if m.get('참가') and m.get('일퇴')]

        # Step 2: 참가 && 늦참이 아닌 사람 중에서, early_participants에 없는 사람
        remaining_slots = 12 - len(early_participants)
        additional_candidates = [
            m for m in members_data
            if m.get('참가') and not m.get('늦참') and m not in early_participants
        ]
        random.shuffle(additional_candidates)
        additional_participants = additional_candidates[:remaining_slots]

        # 최종 매칭 1
        participants_1 = early_participants + additional_participants
        participants_1 = participants_1[:12]

        return render_template(
            'members.html',
            members=members_data,
            participants_1=participants_1
        )

    return render_template('members.html', members=members_data, participants_1=[])

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
