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

    return render_template('index.html', names=names)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
