from flask import Flask, redirect, url_for
from flask_login import LoginManager
from backend.models import db, User
from backend.routes import auth_bp, admin_bp, user_bp, common
import os

def create_app():
    app = Flask(__name__, instance_relative_config=True)
    
    # Ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass
    
    # Configure the SQLite database
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(app.instance_path, 'quiz.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = 'your-secret-key'  # Change this in production
    
    # Initialize database
    db.init_app(app)
    
    # Initialize login manager
    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.init_app(app)
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    # Register blueprints
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(user_bp, url_prefix='/user')
    app.register_blueprint(common, url_prefix='/common')
    
    # Root route
    @app.route('/')
    def home():
        return redirect(url_for('auth.home'))
    
    # Create database tables
    with app.app_context():
        db.create_all()
        
        # Check if admin user exists
        admin = User.query.filter_by(is_admin=True).first()
        if not admin:
            admin = User(
                username='admin@quizmaster.com',
                full_name='Admin User',
                is_admin=True
            )
            admin.set_password('admin123')  # Default password, change this in production
            db.session.add(admin)
            db.session.commit()
            print('Admin user created')
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)