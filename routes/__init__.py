"""初始化"""

from .auth import auth_bp
from .user import user_bp
from .task_routes import task_bp
from .note_routes import note_bp
from .comment_routes import comment_bp
def register_routes(app):
    app.register_blueprint(auth_bp)
    app.register_blueprint(user_bp , url_prefix='/user')
    app.register_blueprint(task_bp)
    app.register_blueprint(note_bp)
    app.register_blueprint(comment_bp)
