from flask import Flask, render_template, request
import pandas as pd
import os
import re
from werkzeug.utils import secure_filename

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route('/', methods=['GET', 'POST'])
def index():
    names = []
    if request.method == 'POST':
        file = request.files['file']
        if file and file.filename.endswith('.xlsx'):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)

            # 엑셀 파일에서 이름 추출
            df = pd.read_excel(filepath, sheet_name=0)
            first_column = df.iloc[:, 0].dropna().astype(str)

            for entry in first_column:
                match = re.match(r"\d+\.\s*(.+)", entry)
                if match:
                    names.append(match.group(1))

            # 기존 코드 중 변경된 부분
            gender_map = {
                "장다민": "여", "양승하": "남", "류재리": "여", "우원석": "남", "남상훈": "남",
                "강민구": "남", "임예지": "여", "이준희": "남", "박대우": "남", "박소현": "여",
                "감사": "남", "나석훈": "남", "임동민": "남", "박은지": "여", "이재현": "남",
                "김나연": "여", "독고혁": "남", "이성훈": "남", "이종욱": "남", "테스": "남"
            }

            # 업로드 후 데이터 추출
            for entry in first_column:
                match = re.match(r"\d+\.\s*(.+)", entry)
                if match:
                    name = match.group(1)
                    names.append(name)

            # 순위 + 이름 + 성별로 묶기
            ranked_names = [
                {"rank": i + 1, "name": name, "gender": gender_map.get(name, "정보 없음")}
                for i, name in enumerate(names)
            ]


    return render_template('index.html', names=names)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
