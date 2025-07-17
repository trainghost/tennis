import os
import json
from pathlib import Path
from typing import Dict, Any

from flask import (
    Flask, render_template, request, redirect, url_for, flash, send_from_directory, session
)
import pandas as pd

# -----------------
# CONFIG
# -----------------
UPLOAD_FOLDER = Path("uploads")
DATA_FOLDER = Path("data")
STATE_JSON = DATA_FOLDER / "player_flags.json"  # 참가/일퇴/늦참 상태 저장
ALLOWED_EXT = {"xlsx"}

# 엑셀 컬럼명 매핑 (엑셀 헤더 -> 내부 키)
# 실제 파일에 맞춰 수정하세요.
COLUMN_MAP = {
    "이름": "name",
    "순위": "rank",
    "승": "win",
    "무": "draw",
    "패": "loss",
    "승점": "points",
}

# 숨길 두번째 열의 원본 엑셀 컬럼명 (예: "성별" / "팀" 등)
HIDE_COL_NAME = "성별"  # 필요 시 None 로 변경

# -----------------
# APP INIT
# -----------------
app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret")
app.config["UPLOAD_FOLDER"] = str(UPLOAD_FOLDER)

UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)
DATA_FOLDER.mkdir(parents=True, exist_ok=True)

# 템플릿 내용 정의
BASE_HTML = """<!doctype html><html>...</html>"""
UPLOAD_HTML = """{% extends 'base.html' %}..."""
TABLE_HTML = """{% extends 'base.html' %}..."""

# 템플릿 생성 함수
def _ensure_templates():
    tdir = Path(app.root_path) / "templates"
    tdir.mkdir(exist_ok=True)
    (tdir / "base.html").write_text(BASE_HTML, encoding="utf-8")
    (tdir / "upload.html").write_text(UPLOAD_HTML, encoding="utf-8")
    (tdir / "table.html").write_text(TABLE_HTML, encoding="utf-8")

# 템플릿 자동 생성 (초기 실행 시)
_ensure_templates()

def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXT


def load_flags() -> Dict[str, Dict[str, bool]]:
    """JSON 파일에서 참가/일퇴/늦참 체크 상태 로드.
    구조: {player_name: {"참가": bool, "일퇴": bool, "늦참": bool}}
    """
    if STATE_JSON.exists():
        try:
            return json.loads(STATE_JSON.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}


def save_flags(flags: Dict[str, Dict[str, bool]]):
    STATE_JSON.write_text(json.dumps(flags, ensure_ascii=False, indent=2), encoding="utf-8")


def read_excel(filepath: Path) -> pd.DataFrame:
    df = pd.read_excel(filepath)
    return df


def normalize_df(df: pd.DataFrame) -> pd.DataFrame:
    """엑셀의 원본 컬럼명을 내부 통일 키로 매핑.
    매핑되지 않은 컬럼은 그대로 둔다.
    """
    renamed = {}
    for col in df.columns:
        if col in COLUMN_MAP:
            renamed[col] = COLUMN_MAP[col]
    df = df.rename(columns=renamed)
    return df


@app.route("/uploads/<path:filename>")
def download_uploaded(filename):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename, as_attachment=True)


@app.route("/", methods=["GET", "POST"])
@app.route("/upload", methods=["GET", "POST"])
def upload_file():
    """엑셀 업로드 후 테이블 표시."""
    if request.method == "POST":
        file = request.files.get("file")
        if not file or file.filename == "":
            flash("파일이 선택되지 않았습니다.")
            return redirect(request.url)
        if not allowed_file(file.filename):
            flash("지원하지 않는 파일 형식입니다. .xlsx 만 가능합니다.")
            return redirect(request.url)

        save_path = UPLOAD_FOLDER / file.filename
        file.save(save_path)
        session["uploaded_filename"] = file.filename  # 세션에 저장
        flash("업로드 완료!")
        return redirect(url_for("view_table"))

    return render_template("upload.html")


@app.route("/table", methods=["GET", "POST"])
def view_table():
    """테이블 표시 & 체크박스 업데이트 처리."""
    filename = session.get("uploaded_filename")
    if not filename:
        flash("먼저 엑셀 파일을 업로드하세요.")
        return redirect(url_for("upload_file"))

    filepath = UPLOAD_FOLDER / filename
    if not filepath.exists():
        flash("업로드된 파일을 찾을 수 없습니다. 다시 업로드하세요.")
        return redirect(url_for("upload_file"))

    df = normalize_df(read_excel(filepath))

    # 숨김 컬럼 제거
    if HIDE_COL_NAME and HIDE_COL_NAME in df.columns:
        df = df.drop(columns=[HIDE_COL_NAME])

    # 체크박스 상태 로드
    flags = load_flags()

    if request.method == "POST":
        # 폼 데이터 처리
        new_flags = {}
        for _, row in df.iterrows():
            name = str(row.get("name") or row.get("이름") or row.get(df.columns[0]))
            참가 = request.form.get(f"chk_participate_{name}") == "on"
            일퇴 = request.form.get(f"chk_earlyleave_{name}") == "on"
            늦참 = request.form.get(f"chk_latestart_{name}") == "on"
            new_flags[name] = {"참가": 참가, "일퇴": 일퇴, "늦참": 늦참}
        save_flags(new_flags)
        flags = new_flags  # 업데이트 반영
        flash("체크 상태가 저장되었습니다.")

    # 렌더에 사용할 행 데이터 준비(dict 리스트)
    records = []
    for _, row in df.iterrows():
        # row -> dict (원본 + flags)
        record = row.to_dict()
        name = str(record.get("name") or record.get("이름") or record.get(df.columns[0]))
        # 플래그 기본값 False
        rec_flag = flags.get(name, {"참가": False, "일퇴": False, "늦참": False})
        record.update({
            "chk_참가": rec_flag.get("참가", False),
            "chk_일퇴": rec_flag.get("일퇴", False),
            "chk_늦참": rec_flag.get("늦참", False),
        })
        records.append(record)

    # 템플릿에 표시할 컬럼 순서 구성
    # 이름은 첫열, 순위 찾기 -> 그 뒤에 체크박스 3개 -> 기존 승/무/패 -> 승점(전체/평균)
    cols = list(df.columns)

    # 내부 map 키 기준으로 위치 파악
    name_col = "name" if "name" in cols else ("이름" if "이름" in cols else cols[0])
    rank_col = "rank" if "rank" in cols else ("순위" if "순위" in cols else None)
    win_col = "win" if "win" in cols else ("승" if "승" in cols else None)
    draw_col = "draw" if "draw" in cols else ("무" if "무" in cols else None)
    loss_col = "loss" if "loss" in cols else ("패" if "패" in cols else None)
    points_col = "points" if "points" in cols else ("승점" if "승점" in cols else None)

    display_cols = [c for c in [name_col, rank_col] if c and c in cols]
    # 체크박스 placeholder 키들은 템플릿에서 직접 처리 -> 여기선 skip
    if win_col: display_cols.append(win_col)
    if draw_col: display_cols.append(draw_col)
    if loss_col: display_cols.append(loss_col)
    if points_col: display_cols.append(points_col)

    # 렌더
    return render_template(
        "table.html",
        records=records,
        display_cols=display_cols,
        name_col=name_col,
        rank_col=rank_col,
        win_col=win_col,
        draw_col=draw_col,
        loss_col=loss_col,
        points_col=points_col,
    )


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
