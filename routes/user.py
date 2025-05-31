"""用户信息增删改查接口模块"""
import pymysql
from flask import Blueprint, request, jsonify
from db import get_db_connection
from routes.token import token_required
from .auth import is_valid_email, is_valid_phone, hash_password

# 创建用户相关路由蓝图
user_bp = Blueprint('user', __name__)


@user_bp.route('/data', methods=['GET'])
@token_required
def get_user_data(user_id):
    """
    获取当前登录用户的信息
    参数:
        user_id - 从 token 装饰器中传入的用户ID
    逻辑:
        - 连接数据库查询用户信息
        - 若用户不存在返回 404
        - 返回用户的基本信息（id, phoneNumber, nickname, email, create_time）
    返回:
        JSON 格式的用户信息或错误提示
    """
    conn = None
    try:
        print(f"请求获取用户数据，user_id = {user_id}")

        conn = get_db_connection()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        cursor.execute("SELECT * FROM user WHERE id = %s", (user_id,))
        user_data = cursor.fetchone()

        if not user_data:
            return jsonify({'error': '用户不存在'}), 404

        user_dict = {
            'id': user_data['id'],
            'phoneNumber': user_data['phoneNumber'],
            'nickname': user_data['nickname'],
            'email': user_data['email'],
            'create_time': str(user_data['create_time'])
        }

        return jsonify(user_dict), 200
    except Exception as e:
        import traceback
        print(f"获取用户数据错误: {str(e)}")
        traceback.print_exc()
        return jsonify({'error': '服务器内部错误'}), 500
    finally:
        if conn:
            conn.close()


@user_bp.route('/update_user', methods=['PUT', 'OPTIONS'])
@token_required
def update_user(user_id):
    """
    更新当前登录用户的信息（手机号、昵称、邮箱、密码）
    支持部分更新，只需提供要更新的字段
    预检请求支持跨域访问

    参数:
        user_id - 从 token 装饰器中传入的用户ID
        请求体 JSON 包含可选字段:
            phone: 新手机号，必须为11位数字
            nickname: 新昵称
            email: 新邮箱，需格式合法
            password: 新密码，将被加密存储

    逻辑:
        - 验证字段格式（手机号、邮箱）
        - 动态构建更新 SQL 语句
        - 执行更新操作，若用户不存在返回 404
        - 返回更新成功消息或错误信息
    """
    if request.method == 'OPTIONS':
        # 处理跨域预检请求
        response = jsonify({'message': '预检成功'})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'PUT')
        return response, 200

    connection = None
    try:
        data = request.get_json()
        phone = data.get('phone')
        nickname = data.get('nickname')
        email = data.get('email')
        password = data.get('password')

        # 构建要更新的字段及对应参数列表
        update_fields = []
        values = []

        # 校验手机号并添加更新字段
        if phone:
            if not is_valid_phone(phone):
                return jsonify({'error': '手机号必须是11位数字'}), 400
            update_fields.append("phoneNumber = %s")
            values.append(phone)

        # 添加昵称更新字段
        if nickname:
            update_fields.append("nickname = %s")
            values.append(nickname)

        # 校验邮箱格式并添加更新字段
        if email:
            if not is_valid_email(email):
                return jsonify({'error': '邮箱格式不正确'}), 400
            update_fields.append("email = %s")
            values.append(email)

        # 加密密码并添加更新字段
        if password:
            encrypted_password = hash_password(password)
            update_fields.append("password = %s")
            values.append(encrypted_password)

        # 如果没有任何更新字段，返回错误
        if not update_fields:
            return jsonify({"error": "至少提供一个要更新的字段"}), 400

        # 拼接完整更新 SQL
        update_sql = f"UPDATE user SET {', '.join(update_fields)} WHERE id = %s"
        values.append(user_id)

        connection = get_db_connection()
        with connection.cursor() as cursor:
            cursor.execute(update_sql, tuple(values))
            connection.commit()

            # 若无更新行，表示用户不存在
            if cursor.rowcount == 0:
                return jsonify({"error": "用户不存在"}), 404

        return jsonify({"message": "更新成功"}), 200

    except Exception as e:
        print(f"更新用户信息错误 : {str(e)}")
        return jsonify({"error": "服务器内部错误"}), 500
    finally:
        if connection:
            connection.close()


@user_bp.route('/delete_user', methods=['DELETE', 'OPTIONS'])
@token_required
def delete_user(user_id):
    """
    注销当前登录用户账号
    预检请求支持跨域访问

    参数:
        user_id - 从 token 装饰器中传入的用户ID

    逻辑:
        - 删除数据库中对应的用户记录
        - 若用户不存在返回 404
        - 返回注销成功消息或错误信息
    """
    if request.method == 'OPTIONS':
        # 跨域预检请求处理
        return jsonify({'message': '预检成功'}), 200

    connection = None
    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            cursor.execute("DELETE FROM user WHERE id = %s", (user_id,))
            connection.commit()
            if cursor.rowcount == 0:
                return jsonify({"error": "用户不存在"}), 404

        return jsonify({"message": "用户已注销"}), 200
    except Exception as e:
        print(f"删除用户错误: {str(e)}")
        return jsonify({"error": "服务器内部错误"}), 500
    finally:
        if connection:
            connection.close()
