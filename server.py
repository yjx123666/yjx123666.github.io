from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import os
from datetime import datetime

app = Flask(__name__)
CORS(app)

# 评论存储文件
COMMENTS_FILE = '/var/www/comments.json'

# 读取评论
def load_comments():
    if os.path.exists(COMMENTS_FILE):
        try:
            with open(COMMENTS_FILE, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                if content:
                    return json.loads(content)
        except (json.JSONDecodeError, IOError):
            pass
    return []

# 保存评论
def save_comments(comments):
    with open(COMMENTS_FILE, 'w', encoding='utf-8') as f:
        json.dump(comments, f, ensure_ascii=False, indent=2)

# 获取所有评论
@app.route('/api/comments', methods=['GET'])
def get_comments():
    comments = load_comments()
    return jsonify(comments)

# 添加评论
@app.route('/api/comments', methods=['POST'])
def add_comment():
    data = request.json
    name = data.get('name', '').strip()
    content = data.get('content', '').strip()

    if not name or not content:
        return jsonify({'error': '昵称和内容不能为空'}), 400

    comments = load_comments()
    new_comment = {
        'id': int(datetime.now().timestamp() * 1000),
        'name': name,
        'content': content,
        'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    comments.insert(0, new_comment)
    save_comments(comments)
    return jsonify(new_comment)

# 删除评论（管理员可删除任意评论，普通用户只能删除自己的）
@app.route('/api/comments/<int:comment_id>', methods=['DELETE'])
def delete_comment(comment_id):
    data = request.json or {}
    requester_name = data.get('name', '').strip()
    admin_pwd = data.get('admin_pwd', '').strip()

    # 管理员密码（与前端一致）
    ADMIN_PASSWORD = 're2026'

    comments = load_comments()
    target = next((c for c in comments if c['id'] == comment_id), None)

    if not target:
        return jsonify({'error': '评论不存在'}), 404

    # 管理员可删除任意评论
    if admin_pwd == ADMIN_PASSWORD:
        comments = [c for c in comments if c['id'] != comment_id]
        save_comments(comments)
        return jsonify({'success': True})

    # 普通用户只能删除自己昵称的评论
    if not requester_name:
        return jsonify({'error': '请提供昵称'}), 403

    if target['name'] != requester_name:
        return jsonify({'error': '只能删除自己的评论'}), 403

    comments = [c for c in comments if c['id'] != comment_id]
    save_comments(comments)
    return jsonify({'success': True})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
