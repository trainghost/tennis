from flask import Flask, render_template, request, redirect, url_for
import pandas as pd
import os
import random

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

members_data = []  # 업로드된 회원 정보

@app.route('/')
def index():
    return render_template('upload.html')

@app.route('/upload', methods=['POST'])
def upload():
    file = request.files['file']
    filepath = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(filepath)
    
    # 업로드된 Excel 파일을 읽어들임
    df = pd.read_excel(filepath)

    # 데이터 리스트로 변환
    global members_data
    members_data = df.to_dict(orient='records')

    return redirect(url_for('members'))  # 업로드 후 /members로 리다이렉트

@app.route('/members', methods=['GET', 'POST'])
def members():
    if request.method == 'POST':
        # 폼에서 받은 체크박스 정보 처리
        for idx, member in enumerate(members_data):
            member['참가'] = 'participate_' + str(idx) in request.form
            member['일퇴'] = 'early_' + str(idx) in request.form
            member['늦참'] = 'late_' + str(idx) in request.form

        # 매칭 1: 참가 체크된 사람 중 일퇴 체크된 사람 우선 뽑기
        participants_early = [m for m in members_data if m.get('참가') and m.get('일퇴')]
        
        # 만약 12명이 안되면 늦참 체크 안 된 사람 중에서 랜덤으로 뽑기
        if len(participants_early) < 12:
            remaining_count = 12 - len(participants_early)
            participants_late = [m for m in members_data if m.get('참가') and not m.get('늦참')]
            additional_participants = random.sample(participants_late, remaining_count)
            participants_early.extend(additional_participants)
        
        # 매칭 1에 해당하는 12명을 선정
        participants_1 = participants_early[:12]

        return render_template('members.html', members=members_data, participants_1=participants_1)
    
    # GET 요청일 경우 (페이지를 처음 로드한 경우)
    return render_template('members.html', members=members_data, participants_1=[])

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
