from flask import Blueprint, request, jsonify
import pymysql
from db import get_db_connection
from routes.token import token_required

comment_bp = Blueprint('comment', __name__)

# 获取当前登录用户的基本信息（ID和昵称）
@comment_bp.route('/user/info', methods=['GET'])
@token_required  # 需要登录，user_id由装饰器注入
def get_user_info(user_id):
    """
    查询并返回当前登录用户的ID和昵称。
    返回：
        成功：用户信息JSON，状态码200
        失败：错误信息，状态码500或提示用户不存在
    """
    try:
        with get_db_connection() as conn:
            with conn.cursor(pymysql.cursors.DictCursor) as cursor:
                cursor.execute("SELECT id, nickname FROM user WHERE id = %s", (user_id,))
                user = cursor.fetchone()
        if user:
            return jsonify({'user': user}), 200
        else:
            return jsonify({'error': '用户不存在'}), 404
    except Exception as e:
        return jsonify({'error': f'服务器错误: {str(e)}'}), 500


# 添加新评论接口
@comment_bp.route('/comments/add', methods=['POST'])
@token_required  # 需登录用户才能添加评论
def add_comment(user_id):
    """
    添加一条评论，评论内容从请求体JSON中获取。
    参数：
        user_id: 当前登录用户ID
        content: 评论内容（必填）
    返回：
        成功：新添加的评论详情及成功消息，状态码201
        失败：错误消息，状态码400（内容为空）或500（服务器错误）
    """
    data = request.get_json()
    content = data.get('content', '')  # 获取评论内容
    if not content:
        return jsonify({'error': '评论内容不能为空'}), 400

    try:
        with get_db_connection() as conn:
            with conn.cursor(pymysql.cursors.DictCursor) as cursor:
                # 插入评论，绑定当前用户ID
                sql = "INSERT INTO comments (content, user_id) VALUES (%s, %s)"
                cursor.execute(sql, (content, user_id))
                conn.commit()
                comment_id = cursor.lastrowid  # 获取新评论ID
                # 查询新插入的评论详情返回
                cursor.execute("SELECT * FROM comments WHERE id = %s", (comment_id,))
                new_comment = cursor.fetchone()
        return jsonify({'message': '评论添加成功', 'comment': new_comment}), 201
    except pymysql.MySQLError as e:
        return jsonify({'error': f'数据库错误: {str(e)}'}), 500
    except Exception as e:
        return jsonify({'error': f'服务器错误: {str(e)}'}), 500


# 删除评论接口
@comment_bp.route('/comments/<int:comment_id>', methods=['DELETE'])
@token_required  # 需登录，且只能删除自己的评论
def delete_comment(user_id, comment_id):
    """
    根据评论ID删除指定评论，确保只能删除属于当前用户的评论。
    参数：
        user_id: 当前登录用户ID
        comment_id: 需要删除的评论ID（路径参数）
    返回：
        成功：删除成功消息，状态码200
        失败：未找到对应评论或无权限删除，状态码404；服务器错误，状态码500
    """
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                # 删除条件：评论ID和用户ID匹配，防止删除他人评论
                sql = "DELETE FROM comments WHERE id = %s AND user_id = %s"
                affected_rows = cursor.execute(sql, (comment_id, user_id))
                conn.commit()
                if affected_rows == 0:
                    return jsonify({'code': 404, 'message': '未找到对应评论'}), 404
        return jsonify({'code': 200, 'message': '评论删除成功'}), 200
    except pymysql.MySQLError as e:
        return jsonify({'code': 500, 'message': f'数据库错误: {str(e)}'}), 500
    except Exception as e:
        return jsonify({'code': 500, 'message': f'服务器错误: {str(e)}'}), 500


# 获取所有评论接口
@comment_bp.route('/comments/list', methods=['GET'])
@token_required  # 可考虑移除装饰器以支持匿名访问
def get_comments(user_id):
    """
    查询并返回所有用户的评论列表，包含评论内容及对应用户昵称。
    返回：
        成功：评论列表JSON，状态码200
        失败：服务器或数据库错误，状态码500
    """
    try:
        with get_db_connection() as conn:
            with conn.cursor(pymysql.cursors.DictCursor) as cursor:
                # 联表查询评论和对应用户昵称，按评论ID倒序排序
                sql = """
                    SELECT c.id, c.content, c.user_id, u.nickname
                    FROM comments c
                    JOIN user u ON c.user_id = u.id
                    ORDER BY c.id DESC
                """
                cursor.execute(sql)
                comments = cursor.fetchall()
        return jsonify({'comments': comments}), 200
    except pymysql.MySQLError as e:
        return jsonify({'error': f'数据库错误: {str(e)}'}), 500
    except Exception as e:
        return jsonify({'error': f'服务器错误: {str(e)}'}), 500
