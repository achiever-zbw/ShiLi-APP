import pymysql.cursors
from flask import request, jsonify, Blueprint
from db import get_db_connection
import jwt
import datetime
import hashlib
from config import config
import time
import re  # 正则库，用于格式校验

auth_bp = Blueprint('auth', __name__)


def hash_password(password: str) -> str:
    """
    使用SHA-256对密码进行哈希加密，避免明文存储。
    :param password: 用户输入的原始密码
    :return: 哈希后的密码字符串
    """
    return hashlib.sha256(password.encode('utf-8')).hexdigest()


def is_valid_phone(phone: str) -> bool:
    """
    校验手机号格式，简单判断是否为11位数字，首位为1，符合中国大陆手机号格式。
    :param phone: 输入手机号字符串
    :return: 校验结果布尔值
    """
    return re.fullmatch(r"^1\d{10}$", phone) is not None


def is_valid_email(email: str) -> bool:
    """
    校验邮箱格式，使用通用邮箱正则表达式匹配。
    :param email: 输入邮箱字符串
    :return: 校验结果布尔值
    """
    return re.fullmatch(r"^[\w\.-]+@[\w\.-]+\.\w+$", email) is not None


@auth_bp.route('/register', methods=['POST'])
def register():
    """
    用户注册接口
    1. 接收手机号、昵称、邮箱、密码、时间戳及防伪标识nonce
    2. 校验参数完整性及格式合法性（手机号、邮箱、请求时间）
    3. 检查数据库是否已存在该手机号或邮箱
    4. 使用SHA256加密密码后存入数据库
    5. 返回注册结果
    """
    connection = None
    try:
        data = request.get_json()
        phone = data.get('phone')
        nickname = data.get('nickname')
        email = data.get('email')
        password = data.get('password')
        timestamp = data.get('timestamp')
        nonce = data.get('nonce')

        # 参数完整性校验
        if not all([phone, nickname, email, password, timestamp, nonce]):
            return jsonify({'error': '缺少必填字段或防伪标识'}), 400

        # 手机号格式校验
        if not is_valid_phone(phone):
            return jsonify({'error': '手机号必须是11位数字'}), 400

        # 邮箱格式校验
        if not is_valid_email(email):
            return jsonify({'error': '邮箱格式不正确'}), 400

        # 时间戳有效性验证，防止请求过期或重放，允许最大时间差10分钟
        now = int(time.time())
        if abs(now - int(timestamp)) > 600:
            return jsonify({'error': '请求已过期'}), 400

        # 获取数据库连接
        connection = get_db_connection()
        with connection.cursor() as cursor:
            # 查询是否已存在该手机号或邮箱的用户，避免重复注册
            cursor.execute("SELECT * FROM user WHERE phoneNumber = %s OR email = %s", (phone, email))
            exist_user = cursor.fetchone()
            if exist_user:
                return jsonify({'error': '用户已存在'}), 409

            encrypted_password = hash_password(password)

            # 插入新用户数据，密码为加密后值，create_time为当前时间
            cursor.execute("""
                INSERT INTO user (phoneNumber, nickname, email, password, create_time)
                VALUES (%s, %s, %s, %s, NOW())
            """, (phone, nickname, email, encrypted_password))
            connection.commit()

        return jsonify({'message': '注册成功'}), 201

    except Exception as e:
        print(f"注册错误: {str(e)}")
        return jsonify({'error': "服务器内部错误"}), 500
    finally:
        if connection:
            connection.close()


@auth_bp.route('/login', methods=['POST'])
def login():
    """
    用户登录接口
    1. 接收手机号和密码
    2. 加密密码后查询数据库
    3. 若验证成功，生成JWT令牌，令牌有效期2小时
    4. 返回用户基本信息及token
    """
    data = request.get_json()
    phoneNumber = data.get('phoneNumber')
    password = data.get('password')
    connection = None
    try:
        encrypted_password = hash_password(password)  # 密码加密

        connection = get_db_connection()
        with connection.cursor(pymysql.cursors.DictCursor) as cursor:
            cursor.execute("SELECT * FROM user WHERE phoneNumber = %s AND password = %s", (phoneNumber, encrypted_password))
            user = cursor.fetchone()
            if user:
                payload = {
                    'user_id': user['id'],
                    'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=2)
                }
                # secret_key为配置中敏感字段，生产环境建议从环境变量读取或安全存储
                token = jwt.encode(payload, config['secret_key'], algorithm='HS256')
                user_data = {
                    'id': user['id'],
                    'nickname': user['nickname'],
                    'email': user['email'],
                    'phoneNumber': user['phoneNumber']
                }
                return jsonify({
                    "message": "登录成功",
                    "token": token,
                    "user": user_data
                }), 200
            else:
                return jsonify({"error": "账号或密码错误"}), 401
    except Exception as e:
        print(f"登录错误: {str(e)}")
        return jsonify({"error": "服务器内部错误"}), 500
    finally:
        if connection:
            connection.close()


@auth_bp.route('/reset_password', methods=['POST', 'OPTIONS'])
def reset_password():
    """
    忘记密码接口，重置用户密码
    1. 支持OPTIONS预检请求
    2. 接收手机号和新密码
    3. 校验手机号格式和参数完整性
    4. 加密新密码更新数据库对应用户
    5. 返回重置结果
    """
    if request.method == 'OPTIONS':
        return jsonify({'message': '预检成功'}), 200

    connection = None
    try:
        data = request.get_json()
        phone = data.get('phone')
        new_password = data.get('new_password')

        if not phone or not new_password:
            return jsonify({"error": "手机号和新密码不能为空"}), 400

        if not is_valid_phone(phone):
            return jsonify({"error": "手机号格式不正确"}), 400

        encrypted_password = hash_password(new_password)

        connection = get_db_connection()
        with connection.cursor() as cursor:
            cursor.execute("""
                UPDATE user
                SET password = %s
                WHERE phoneNumber = %s
            """, (encrypted_password, phone))
            connection.commit()

            if cursor.rowcount == 0:
                return jsonify({"error": "手机号未注册"}), 404

        return jsonify({"message": "密码已重置，请重新登录"}), 200
    except Exception as e:
        print(f"重置密码出错: {str(e)}")
        return jsonify({"error": "服务器内部错误"}), 500
    finally:
        if connection:
            connection.close()
