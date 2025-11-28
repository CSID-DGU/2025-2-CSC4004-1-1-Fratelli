# linux_ai_server.py
from flask import Flask, request, send_file
import io

app = Flask(__name__)

@app.route('/protect_voice', methods=['POST'])
def protect_voice():
    # AI 처리 코드
    return send_file(...)

if __name__ == '__main__':
    # 8080, 5000, 8000 등 1024 이상 포트 사용
    app.run(host='0.0.0.0', port=8080)  # sudo 불필요!