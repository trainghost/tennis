from flask import Flask, render_template, request
import pandas as pd
import os
import re
from werkzeug.utils import secure_filename
import random

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route('/submit', methods=['POST'])
def submit_attendance():
    results = []

    for i in range(1, 100):  # 최대 100명까지 탐색
        key = f'attendance_{i}[]'
        if key in request.form:
            attendance_values = request.form.getlist(key)
            results.append({
                "rank": i,
                "status": attendance_values  # 참가, 일퇴, 늦참 등이 들어 있는 리스트
            })

    return render_template('submitted.html', results=results)


@app.route('/', methods=['GET', 'POST'])
def index():
    ranked_names = []
    if request.method == 'POST':
        file = request.files['file']
        if file and file.filename.endswith('.xlsx'):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)

            df = pd.read_excel(filepath, sheet_name=0)
            first_column = df.iloc[:, 0].dropna().astype(str)

            gender_map = {
                "장다민": "여", "양승하": "남", "류재리": "여", "우원석": "남", "남상훈": "남",
                "강민구": "남", "임예지": "여", "이준희": "남", "박대우": "남", "박소현": "여",
                "감사": "남", "나석훈": "남", "임동민": "남", "박은지": "여", "이재현": "남",
                "김나연": "여", "독고혁": "남", "이성훈": "남", "이종욱": "남", "테스": "남"
            }

            extracted_names = []
            for entry in first_column:
                match = re.match(r"\d+\.\s*(.+)", entry)
                if match:
                    extracted_names.append(match.group(1))

            ranked_names = [
                {"rank": i + 1, "name": name, "gender": gender_map.get(name, "정보 없음")}
                for i, name in enumerate(extracted_names)
            ]

    return render_template('index.html', names=ranked_names)



@app.route('/submit', methods=['POST'])
def submit_attendance():
    results = []
    group1 = []
    group2 = []
    group3 = []

    # 모든 참석 데이터 추출
    attendees = []
    for i in range(1, 100):  # 최대 100명까지 탐색
        key = f'attendance_{i}[]'
        if key in request.form:
            attendance_values = request.form.getlist(key)
            name = f"Person {i}"  # 이름을 생성해 둔 예시 (실제 코드에서는 이름을 사용)
            status = {
                "rank": i,
                "status": attendance_values
            }
            attendees.append(status)

    # 그룹 분류
    for attendee in attendees:
        status = attendee['status']
        rank = attendee['rank']

        # 그룹 1 조건: 참가, 일퇴 체크, 늦참 체크 안함
        if "참가" in status and "일퇴" in status and "늦참" not in status:
            group1.append(attendee)
        
        # 그룹 2 조건: 참가 체크하고, 그룹 1에 포함되지 않음
        elif "참가" in status and attendee not in group1:
            if "늦참" in status:
                group2.append(attendee)
            elif "일퇴" in status:
                group2.append(attendee)

        # 그룹 3 조건: 참가 체크하고, 그룹 1, 2에 포함되지 않음
        elif "참가" in status and attendee not in group1 and attendee not in group2:
            group3.append(attendee)

    # 1그룹 채우기 (최소 12명)
    if len(group1) < 12:
        # 참가 체크하고, 늦참 체크 안한 사람 중에서 랜덤으로 추가
        available_for_group1 = [attendee for attendee in attendees if "참가" in attendee['status'] and "늦참" not in attendee['status'] and attendee not in group1]
        additional_needed = 12 - len(group1)
        group1.extend(random.sample(available_for_group1, additional_needed))

    # 2그룹 채우기 (최소 12명)
    if len(group2) < 12:
        # 1그룹에 포함되지 않은 참가 체크한 사람 중에서 채우기
        available_for_group2 = [attendee for attendee in attendees if "참가" in attendee['status'] and attendee not in group1 and attendee not in group2]
        if len(group2) + len(available_for_group2) < 12:
            # 부족하면 늦참 체크한 사람부터 채움
            available_for_group2.extend([attendee for attendee in attendees if "참가" in attendee['status'] and "늦참" in attendee['status'] and attendee not in group1 and attendee not in group2])
        additional_needed = 12 - len(group2)
        group2.extend(random.sample(available_for_group2, additional_needed))

    # 3그룹 채우기 (최소 12명)
    if len(group3) < 12:
        # 2그룹에 포함되지 않은 참가 체크한 사람 중에서 채우기
        available_for_group3 = [attendee for attendee in attendees if "참가" in attendee['status'] and attendee not in group1 and attendee not in group2]
        if len(group3) + len(available_for_group3) < 12:
            # 부족하면 늦참 체크한 사람부터 채움
            available_for_group3.extend([attendee for attendee in attendees if "참가" in attendee['status'] and "늦참" in attendee['status'] and attendee not in group1 and attendee not in group2])
        if len(group3) + len(available_for_group3) < 12:
            # 부족하면 일퇴 체크한 사람부터 채움
            available_for_group3.extend([attendee for attendee in attendees if "참가" in attendee['status'] and "일퇴" in attendee['status'] and attendee not in group1 and attendee not in group2])
        additional_needed = 12 - len(group3)
        group3.extend(random.sample(available_for_group3, additional_needed))

    # 결과를 템플릿에 전달
    results = {
        'group1': group1,
        'group2': group2,
        'group3': group3
    }

    return render_template('submitted.html', results=results)


if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
