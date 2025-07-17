from flask import Flask, render_template, request, redirect, url_for
import pandas as pd
import os

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

    return redirect(url_for('members'))  # 여기서 members 페이지로 리다이렉트

@app.route('/members', methods=['GET', 'POST'])
def members():
    if request.method == 'POST':
        # 폼에서 받은 체크박스 정보 처리
        for idx, member in enumerate(members_data):
            member['참가'] = 'participate_' + str(idx) in request.form
            member['일퇴'] = 'early_' + str(idx) in request.form
            member['늦참'] = 'late_' + str(idx) in request.form

        # 여기에 매칭 로직을 추가하면 됩니다
        participants_1 = [m for m in members_data if m.get('참가')]  # 예시로 참가한 회원들만 추출
        participants_2 = [m for m in members_data if not m.get('참가')]  # 참가하지 않은 회원들

        return render_template('members.html', members=members_data, participants_1=participants_1, participants_2=participants_2)
    
    # GET 요청일 경우 (페이지를 처음 로드한 경우)
    return render_template('members.html', members=members_data, participants_1=[], participants_2=[])

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
