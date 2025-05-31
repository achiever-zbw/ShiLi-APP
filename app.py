from flask import Flask, request
from flask_cors import CORS
from routes import register_routes
import jwt

app = Flask(__name__)

# 配置CORS
CORS(app, resources={r"/*": {"origins": "*", "allow_headers": ["Content-Type", "Authorization", "Access-Control-Allow-Origin", "Access-Control-Allow-Headers", "Access-Control-Allow-Methods"]}}, supports_credentials=True)

# 添加全局的CORS预检请求处理
@app.before_request
def before_request():
    if request.method == 'OPTIONS':
        response = app.make_default_options_response()
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, Access-Control-Allow-Origin, Access-Control-Allow-Headers, Access-Control-Allow-Methods'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
        return response

register_routes(app)

if __name__ == '__main__':
    app.run(debug=True , host='0.0.0.0' , port=5000)