from flask import Blueprint, jsonify, request
from datetime import datetime, timedelta
import pymysql
from db import get_db_connection
from routes.token import token_required

task_bp = Blueprint('task', __name__)

# 添加任务接口
@task_bp.route('/task/add', methods=['POST'])
@token_required
def add_task(user_id):
    """
    添加新任务接口
    - 从请求中获取任务相关字段：title(必需), description(可选), due_date(可选), tag(可选), status(可选，默认'pending')
    - 解析 due_date 字符串，支持 ISO 格式和标准格式，做时区调整
    - 将任务信息插入数据库，并返回新创建的任务信息
    - 错误时返回对应的错误信息和状态码
    """
    try:
        data = request.get_json()
        title = data['title']
        description = data.get('description', '')
        due_date = data.get('due_date')  # 可能为 None 或空字符串
        tag = data.get('tag', '')
        status = data.get('status', 'pending')

        if not title:
            return jsonify({'error': '缺少任务标题'}), 400

        # 处理截止日期格式及时区调整
        if due_date:
            try:
                if 'T' in due_date:
                    due_date = datetime.strptime(due_date.replace('T', ' '), '%Y-%m-%d %H:%M')
                else:
                    due_date = datetime.strptime(due_date, '%Y-%m-%d %H:%M:%S')
                due_date -= timedelta(hours=8)  # 调整时区（如有需要）
            except ValueError:
                return jsonify({'error': '无效的截止日期格式，应为 YYYY-MM-DD HH:MM:SS'}), 400
        else:
            due_date = None

        # 插入数据库
        with get_db_connection() as conn:
            with conn.cursor(pymysql.cursors.DictCursor) as cursor:
                query = """
                    INSERT INTO task (user_id, title, description, due_date, tag, status)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """
                cursor.execute(query, (user_id, title, description, due_date, tag, status))
                task_id = cursor.lastrowid
                conn.commit()

                # 查询并返回刚插入的任务
                cursor.execute("SELECT * FROM task WHERE id = %s", (task_id,))
                task = cursor.fetchone()

        return jsonify({'message': '任务添加成功', 'task': task}), 201
    except pymysql.MySQLError as e:
        print(f"MySQL error: {str(e)}")  # 调试日志
        return jsonify({'error': f'MySQL 错误: {str(e)}'}), 500
    except Exception as e:
        print(f"Server error: {str(e)}")  # 调试日志
        return jsonify({'error': f'服务器错误: {str(e)}'}), 500

# 更新任务接口
@task_bp.route('/task/update', methods=['PUT'])
@token_required
def update_task(user_id):
    """
    更新任务接口
    - 从请求中获取 task_id 和需更新的字段
    - 根据 task_id 和 user_id 定位任务，执行更新操作
    - 返回更新后的任务信息
    - 若缺少 task_id 或无更新字段，返回对应错误
    """
    try:
        data = request.get_json()
        task_id = data.get('task_id')

        if not task_id:
            return jsonify({'error': '缺少任务ID'}), 400

        update_data = {}
        for key in ["title", "description", "due_date", "tag", "status"]:
            value = data.get(key)
            if value is not None:
                update_data[key] = value

        if not update_data:
            return jsonify({'error': '没有提供要更新的字段'}), 400

        # 动态生成 SQL 语句中的 SET 部分和参数列表
        set_clause = ', '.join(f"{field} = %s" for field in update_data)
        values = list(update_data.values())
        values.extend([task_id, user_id])

        conn = get_db_connection()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        query = f"""
            UPDATE task SET {set_clause}
            WHERE id = %s AND user_id = %s
        """
        cursor.execute(query, tuple(values))
        conn.commit()

        # 查询更新后的任务信息
        cursor.execute("SELECT * FROM task WHERE id = %s AND user_id = %s", (task_id, user_id))
        updated_task = cursor.fetchone()

        cursor.close()
        conn.close()

        return jsonify({'message': '任务更新成功', 'task': updated_task}), 200
    except pymysql.MySQLError as e:
        return jsonify({'error': f'MySQL 错误: {str(e)}'}), 500
    except Exception as e:
        return jsonify({'error': f'服务器错误: {str(e)}'}), 500

# 获取任务列表接口
@task_bp.route('/task/list', methods=['GET'])
@token_required
def get_task_list(user_id):
    """
    获取任务列表接口
    - 支持根据状态(status)、标签(tag)、关键字(search)过滤任务
    - 返回当前用户符合条件的所有任务列表
    """
    try:
        status = request.args.get('status')
        tag = request.args.get('tag')
        search = request.args.get('search')

        with get_db_connection() as conn:
            with conn.cursor(pymysql.cursors.DictCursor) as cursor:
                query = "SELECT * FROM task WHERE user_id = %s"
                params = [user_id]

                # 根据请求参数拼接查询条件
                if status:
                    query += " AND status = %s"
                    params.append(status)
                if tag:
                    query += " AND tag = %s"
                    params.append(tag)
                if search:
                    query += " AND (title LIKE %s OR description LIKE %s)"
                    keyword = f"%{search}%"
                    params.extend([keyword, keyword])

                cursor.execute(query, tuple(params))
                tasks = cursor.fetchall()

        return jsonify({'tasks': tasks}), 200
    except pymysql.MySQLError as e:
        return jsonify({'error': f'MySQL 错误: {str(e)}'}), 500
    except Exception as e:
        return jsonify({'error': f'服务器错误: {str(e)}'}), 500

# 删除任务接口
@task_bp.route('/task/delete/<int:task_id>', methods=['DELETE'])
@token_required
def delete_task(user_id, task_id):
    """
    删除任务接口
    - 根据任务ID和用户ID，删除对应任务
    - 若任务不存在或用户无权限，返回404错误
    - 成功删除返回成功消息
    """
    try:
        with get_db_connection() as conn:
            with conn.cursor(pymysql.cursors.DictCursor) as cursor:
                # 验证任务是否存在且属于该用户
                cursor.execute("SELECT * FROM task WHERE id = %s AND user_id = %s", (task_id, user_id))
                task = cursor.fetchone()
                if not task:
                    return jsonify({'error': '任务不存在或无权限'}), 404

                # 删除任务
                cursor.execute("DELETE FROM task WHERE id = %s AND user_id = %s", (task_id, user_id))
                conn.commit()

        return jsonify({'message': '任务删除成功'}), 200
    except pymysql.MySQLError as e:
        return jsonify({'error': f'MySQL 错误: {str(e)}'}), 500
    except Exception as e:
        return jsonify({'error': f'服务器错误: {str(e)}'}), 500
