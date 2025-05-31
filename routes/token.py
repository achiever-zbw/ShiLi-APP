from flask import request, jsonify
from functools import wraps
import jwt
from config import config

def token_required(f):
    """
    装饰器函数，验证请求中的 JWT token 是否有效。
    1. 从请求头中获取 Authorization 字段，格式应为 "Bearer <token>"。
    2. 解析并验证 JWT token，确保其未过期且合法。
    3. 从 token 中提取 user_id 并作为第一个参数传递给被装饰的视图函数。
    4. 若 token 缺失、格式错误、过期或无效，则返回相应的错误响应。

    用法示例：
    @token_required
    def some_route(user_id):
        pass

    :param f: 需要装饰的视图函数
    :return: 包装后的函数
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        # 获取请求头中的 Authorization 字段
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            # 如果没有提供 token，返回 403 错误
            return jsonify({'error': 'Token is missing'}), 403

        try:
            # 从 "Bearer <token>" 格式中分割出实际的 token
            token = auth_header.split(" ")[1]
            # 验证并解码 token，获取负载信息
            data = jwt.decode(token, config['secret_key'], algorithms=['HS256'])
            # 从解码后的数据中获取用户 ID
            user_id = data['user_id']
        except IndexError:
            # 处理 Authorization 格式不正确的异常
            return jsonify({'error': 'Token 格式错误，应为 Bearer <token>'}), 403
        except jwt.ExpiredSignatureError:
            # 处理 token 过期异常
            return jsonify({'error': 'Token 已过期'}), 403
        except jwt.InvalidTokenError as e:
            # 处理其他无效 token 异常
            return jsonify({'error': f'无效的 token: {str(e)}'}), 403

        # 验证通过，将 user_id 作为第一个参数传递给被装饰函数
        return f(user_id, *args, **kwargs)

    return decorated
