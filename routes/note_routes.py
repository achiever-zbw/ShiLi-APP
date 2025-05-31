from flask import request, Blueprint, jsonify
from jwt import ExpiredSignatureError
from db import get_db_connection
import pymysql
from functools import wraps
from routes.token import token_required

# 封装笔记模块的所有接口
note_bp = Blueprint('note', __name__)


# 1.创建新笔记
@note_bp.route('/note/add', methods=['POST'])
@token_required
def add_note(user_id):
    """
    添加笔记接口，创建笔记并存入数据库
    :param user_id: 当前登录用户的ID（通过token_required装饰器注入）
    :return: JSON格式的操作结果及新创建的笔记信息
    """
    data = request.get_json()  # 获取请求中传来的JSON数据（笔记内容）
    title = data.get('title')  # 获取标题
    content = data.get('content', '')  # 获取内容，默认为空字符串
    if not title:
        return jsonify({'error': '标题不能为空'}), 400  # 标题为空返回错误

    try:
        # 获取数据库连接，执行插入操作
        with get_db_connection() as conn:
            with conn.cursor(pymysql.cursors.DictCursor) as cursor:
                # 插入新笔记（标题，内容，所属用户）
                sql = """
                    INSERT INTO notes (title, content, user_id) VALUES (%s, %s, %s)
                """
                cursor.execute(sql, (title, content, user_id))
                conn.commit()

                # 获取刚插入的笔记ID，并查询新笔记详细信息返回
                note_id = cursor.lastrowid
                cursor.execute("SELECT * FROM notes WHERE id = %s", (note_id,))
                new_note = cursor.fetchone()
        return jsonify({'message': '笔记创建成功', 'note': new_note}), 201
    except pymysql.MySQLError as e:
        return jsonify({'error': f'数据库错误 : {str(e)}'}), 500
    except Exception as e:
        return jsonify({'error': f'服务器错误: {str(e)}'}), 500


# 2.获取当前用户所有笔记标题列表
@note_bp.route('/note/list', methods=['GET'])
@token_required
def get_note(user_id):
    """
    获取当前用户的所有笔记标题及ID，用于前端展示笔记列表
    :param user_id: 当前登录用户的ID
    :return: JSON格式的笔记列表
    """
    try:
        with get_db_connection() as conn:
            with conn.cursor(pymysql.cursors.DictCursor) as cursor:
                # 查询当前用户所有笔记的ID和标题，按ID倒序排列
                cursor.execute("SELECT id, title FROM notes WHERE user_id = %s ORDER BY id DESC", (user_id,))
                notes = cursor.fetchall()
        return jsonify({'notes': notes}), 200
    except pymysql.MySQLError as e:
        return jsonify({'error': f'数据库错误 : {str(e)}'}), 500
    except Exception as e:
        return jsonify({'error': f'服务器错误: {str(e)}'}), 500


# 3. 获取笔记内容
@note_bp.route('/note/<int:note_id>', methods=['GET'])
@token_required
def get_note_content(user_id, note_id):
    """
    获取指定ID的笔记详细内容，确保属于当前用户
    :param user_id: 当前用户ID
    :param note_id: 要查询的笔记ID
    :return: JSON格式的笔记详细信息或错误信息
    """
    try:
        with get_db_connection() as conn:
            with conn.cursor(pymysql.cursors.DictCursor) as cursor:
                # 根据笔记ID和用户ID查询笔记，确保用户只能访问自己的笔记
                cursor.execute("SELECT * FROM notes WHERE id = %s AND user_id = %s", (note_id, user_id))
                note = cursor.fetchone()
        if not note:
            return jsonify({'error': '未找到对应笔记'}), 404
        return jsonify({'note': note}), 200
    except pymysql.MySQLError as e:
        return jsonify({'error': f'数据库错误: {str(e)}'}), 500
    except Exception as e:
        return jsonify({'error': f'服务器错误: {str(e)}'}), 500


# 4. 更新笔记内容
@note_bp.route('/note/<int:note_id>', methods=['PUT'])
@token_required
def update_note(user_id, note_id):
    """
    根据笔记ID更新该笔记的标题和内容，确保该笔记属于当前用户
    :param user_id: 当前用户ID
    :param note_id: 要更新的笔记ID
    :return: 更新后的笔记信息或错误提示
    """
    data = request.get_json()
    title = data.get('title')
    content = data.get('content')

    if not title:
        return jsonify({'error': '标题不能为空'}), 400

    try:
        with get_db_connection() as conn:
            with conn.cursor(pymysql.cursors.DictCursor) as cursor:
                # 先确认该笔记存在且属于当前用户
                cursor.execute("SELECT * FROM notes WHERE id = %s AND user_id = %s", (note_id, user_id))
                note = cursor.fetchone()
                if not note:
                    return jsonify({'error': '未找到对应笔记'}), 404

                # 更新笔记标题、内容，并更新时间
                sql = """
                    UPDATE notes SET title = %s, content = %s, updated_at = NOW()
                    WHERE id = %s AND user_id = %s
                """
                cursor.execute(sql, (title, content, note_id, user_id))
                conn.commit()

                # 查询更新后的笔记返回给前端
                cursor.execute("SELECT * FROM notes WHERE id = %s AND user_id = %s", (note_id, user_id))
                updated_note = cursor.fetchone()
        return jsonify({'message': '笔记更新成功', 'note': updated_note}), 200
    except pymysql.MySQLError as e:
        return jsonify({'error': f'数据库错误: {str(e)}'}), 500
    except Exception as e:
        return jsonify({'error': f'服务器错误: {str(e)}'}), 500


# 5. 删除笔记
@note_bp.route('/note/<int:note_id>', methods=['DELETE'])
@token_required
def delete_note(user_id, note_id):
    """
    删除指定ID的笔记，确保只有笔记所属用户可以删除
    :param user_id: 当前用户ID
    :param note_id: 要删除的笔记ID
    :return: 删除成功或失败的状态及提示信息
    """
    try:
        with get_db_connection() as conn:
            with conn.cursor(pymysql.cursors.DictCursor) as cursor:
                # 根据笔记ID和用户ID删除笔记，确保只能删除自己的笔记
                sql = """
                    DELETE FROM notes WHERE id = %s AND user_id = %s
                """
                affected_rows = cursor.execute(sql, (note_id, user_id))
                conn.commit()

                if affected_rows == 0:
                    return jsonify({'code': 404, 'message': '未找到对应笔记'}), 404

        return jsonify({'code': 200, 'message': '笔记删除成功'}), 200
    except pymysql.MySQLError as e:
        return jsonify({'code': 500, 'message': f'数据库错误: {str(e)}'}), 500
    except Exception as e:
        return jsonify({'code': 500, 'message': f'服务器错误: {str(e)}'}), 500
