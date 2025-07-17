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

    # 참가한 사람들 필터링
    participants = [member for member in members_data if member.get('참가')]

    # 참가자 목록 출력 (디버깅용)
    print("참가한 사람들:", participants)

    return render_template('members.html', members=members_data, participants=participants)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
