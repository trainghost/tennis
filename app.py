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
    
    return redirect(url_for('members'))

@app.route('/members', methods=['GET', 'POST'])
def members():
    if request.method == 'POST':
        updated_data = []
        for i, member in enumerate(members_data):
            member['참가'] = request.form.get(f'participate_{i}') == 'on'
            member['일퇴'] = request.form.get(f'early_{i}') == 'on'
            member['늦참'] = request.form.get(f'late_{i}') == 'on'
            updated_data.append(member)

        # JSON으로 저장
        with open('members.json', 'w', encoding='utf-8') as f:
            json.dump(updated_data, f, ensure_ascii=False, indent=2)

        return "저장 완료!"

    return render_template('members.html', members=members_data)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
