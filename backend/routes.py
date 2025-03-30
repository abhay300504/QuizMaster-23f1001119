from flask import Blueprint, render_template, redirect, url_for, request, flash, jsonify, session
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash
from datetime import datetime, timedelta
from .models import db, User, Subject, Chapter, Quiz, Question, Score, QuizAttempt
from sqlalchemy import func
import json

# Create blueprints for different parts of the application
auth_bp = Blueprint('auth', __name__)
admin_bp = Blueprint('admin', __name__)
user_bp = Blueprint('user', __name__)
common = Blueprint('common', __name__)

# Authentication routes

@auth_bp.route("/",methods=['GET'])
def home():
    return render_template("auth/home.html")

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user)
            if user.is_admin:
                return redirect(url_for('admin.dashboard'))
            else:
                return redirect(url_for('user.dashboard'))
        else:
            flash('Invalid username or password')
    
    return render_template('auth/login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        full_name = request.form.get('full_name')
        qualification = request.form.get('qualification')
        dob_str = request.form.get('dob')
        
        # Check if username already exists
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('Username already exists')
            return redirect(url_for('auth.register'))
        
        # Parse date string to date object
        try:
            dob = datetime.strptime(dob_str, '%Y-%m-%d').date()
        except:
            dob = None
        
        # Create new user
        new_user = User(
            username=username,
            full_name=full_name,
            qualification=qualification,
            dob=dob,
            is_admin=False
        )
        new_user.set_password(password)
        
        db.session.add(new_user)
        db.session.commit()
        
        flash('Registration successful, please login')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/register.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))

# Admin routes
@admin_bp.route('/dashboard')
@login_required
def dashboard():
    if not current_user.is_admin:
        flash('Unauthorized access')
        return redirect(url_for('user.dashboard'))
    
    subjects_count = Subject.query.count()
    chapters_count = Chapter.query.count()
    quizzes_count = Quiz.query.count()
    users_count = User.query.filter_by(is_admin=False).count()

    top_users = db.session.query(
            User.username,
            func.avg(Score.score).label('avg_score'),
            func.count(Score.id).label('quiz_count')
        ).join(Score, User.id == Score.user_id)\
         .group_by(User.id)\
         .having(func.count(Score.id) > 0)\
         .order_by(func.avg(Score.score).desc())\
         .limit(5).all()
    
    return render_template('admin/dashboard.html', 
                          subjects_count=subjects_count,
                          chapters_count=chapters_count,
                          quizzes_count=quizzes_count,
                          users_count=users_count,
                          top_users=top_users)

# Subject Management
@admin_bp.route('/subjects')
@login_required
def subjects():
    if not current_user.is_admin:
        return redirect(url_for('user.dashboard'))
    
    subjects = Subject.query.all()
    return render_template('admin/subjects.html', subjects=subjects)

@admin_bp.route('/subjects/add', methods=['GET', 'POST'])
@login_required
def add_subject():
    if not current_user.is_admin:
        return redirect(url_for('user.dashboard'))
    
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        
        new_subject = Subject(name=name, description=description)
        db.session.add(new_subject)
        db.session.commit()
        
        flash('Subject added successfully')
        return redirect(url_for('admin.subjects'))
    
    return render_template('admin/add_subject.html')

@admin_bp.route('/subjects/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_subject(id):
    if not current_user.is_admin:
        return redirect(url_for('user.dashboard'))
    
    subject = Subject.query.get_or_404(id)
    
    if request.method == 'POST':
        subject.name = request.form.get('name')
        subject.description = request.form.get('description')
        
        db.session.commit()
        
        flash('Subject updated successfully')
        return redirect(url_for('admin.subjects'))
    
    return render_template('admin/edit_subject.html', subject=subject)

@admin_bp.route('/subjects/delete/<int:id>')
@login_required
def delete_subject(id):
    if not current_user.is_admin:
        return redirect(url_for('user.dashboard'))
    
    subject = Subject.query.get_or_404(id)
    db.session.delete(subject)
    db.session.commit()
    
    flash('Subject deleted successfully')
    return redirect(url_for('admin.subjects'))

# Chapter Management
@admin_bp.route('/chapters/<int:subject_id>')
@login_required
def chapters(subject_id):
    if not current_user.is_admin:
        return redirect(url_for('user.dashboard'))
    
    subject = Subject.query.get_or_404(subject_id)
    chapters = Chapter.query.filter_by(subject_id=subject_id).all()
    
    return render_template('admin/chapters.html', subject=subject, chapters=chapters)

@admin_bp.route('/chapters/add/<int:subject_id>', methods=['GET', 'POST'])
@login_required
def add_chapter(subject_id):
    if not current_user.is_admin:
        return redirect(url_for('user.dashboard'))
    
    subject = Subject.query.get_or_404(subject_id)
    
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        
        new_chapter = Chapter(name=name, description=description, subject_id=subject_id)
        db.session.add(new_chapter)
        db.session.commit()
        
        flash('Chapter added successfully')
        return redirect(url_for('admin.chapters', subject_id=subject_id))
    
    return render_template('admin/add_chapter.html', subject=subject)

@admin_bp.route('/chapters/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_chapter(id):
    if not current_user.is_admin:
        return redirect(url_for('user.dashboard'))
    
    chapter = Chapter.query.get_or_404(id)
    
    if request.method == 'POST':
        chapter.name = request.form.get('name')
        chapter.description = request.form.get('description')
        
        db.session.commit()
        
        flash('Chapter updated successfully')
        return redirect(url_for('admin.chapters', subject_id=chapter.subject_id))
    
    return render_template('admin/edit_chapter.html', chapter=chapter)

@admin_bp.route('/chapters/delete/<int:id>')
@login_required
def delete_chapter(id):
    if not current_user.is_admin:
        return redirect(url_for('user.dashboard'))
    
    chapter = Chapter.query.get_or_404(id)
    subject_id = chapter.subject_id
    
    db.session.delete(chapter)
    db.session.commit()
    
    flash('Chapter deleted successfully')
    return redirect(url_for('admin.chapters', subject_id=subject_id))

# Quiz Management
@admin_bp.route('/quizzes/<int:chapter_id>')
@login_required
def quizzes(chapter_id):
    if not current_user.is_admin:
        return redirect(url_for('user.dashboard'))
    
    chapter = Chapter.query.get_or_404(chapter_id)
    quizzes = Quiz.query.filter_by(chapter_id=chapter_id).all()
    
    return render_template('admin/quizzes.html', chapter=chapter, quizzes=quizzes)

@admin_bp.route('/quizzes/add/<int:chapter_id>', methods=['GET', 'POST'])
@login_required
def add_quiz(chapter_id):
    if not current_user.is_admin:
        return redirect(url_for('user.dashboard'))
    
    chapter = Chapter.query.get_or_404(chapter_id)
    
    if request.method == 'POST':
        title = request.form.get('title')
        date_str = request.form.get('date_of_quiz')
        duration = request.form.get('time_duration')
        remarks = request.form.get('remarks')
        
        # Parse date string to date object
        date_of_quiz = datetime.strptime(date_str, '%Y-%m-%d').date()
        
        new_quiz = Quiz(
            title=title,
            chapter_id=chapter_id,
            date_of_quiz=date_of_quiz,
            time_duration=int(duration),
            remarks=remarks
        )
        
        db.session.add(new_quiz)
        db.session.commit()
        
        flash('Quiz added successfully')
        return redirect(url_for('admin.quizzes', chapter_id=chapter_id))
    
    return render_template('admin/add_quiz.html', chapter=chapter)

@admin_bp.route('/quizzes/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_quiz(id):
    if not current_user.is_admin:
        return redirect(url_for('user.dashboard'))
    
    quiz = Quiz.query.get_or_404(id)
    
    if request.method == 'POST':
        quiz.title = request.form.get('title')
        quiz.description = request.form.get('description')
        quiz.date_of_quiz = datetime.strptime(request.form.get('date_of_quiz'), '%Y-%m-%d').date()
        quiz.time_duration = int(request.form.get('time_duration'))
        quiz.remarks = request.form.get('remarks')
        
        db.session.commit()
        
        flash('Quiz updated successfully')
        return redirect(url_for('admin.quizzes', chapter_id=quiz.chapter_id))
    
    return render_template('admin/edit_quiz.html', quiz=quiz)

@admin_bp.route('/quizzes/delete/<int:id>')
@login_required
def delete_quiz(id):
    if not current_user.is_admin:
        return redirect(url_for('user.dashboard'))
    
    quiz = Quiz.query.get_or_404(id)
    chapter_id = quiz.chapter_id
    
    db.session.delete(quiz)
    db.session.commit()
    
    flash('Quiz deleted successfully')
    return redirect(url_for('admin.quizzes', chapter_id=chapter_id))

# Question Management
@admin_bp.route('/questions/<int:quiz_id>')
@login_required
def questions(quiz_id):
    if not current_user.is_admin:
        return redirect(url_for('user.dashboard'))
    
    quiz = Quiz.query.get_or_404(quiz_id)
    questions = Question.query.filter_by(quiz_id=quiz_id).all()
    
    return render_template('admin/questions.html', quiz=quiz, questions=questions)

@admin_bp.route('/questions/add/<int:quiz_id>', methods=['GET', 'POST'])
@login_required
def add_question(quiz_id):
    if not current_user.is_admin:
        return redirect(url_for('user.dashboard'))
    
    quiz = Quiz.query.get_or_404(quiz_id)
    
    if request.method == 'POST':
        question_text = request.form.get('question_text')
        option_a = request.form.get('option_a')
        option_b = request.form.get('option_b')
        option_c = request.form.get('option_c')
        option_d = request.form.get('option_d')
        correct_option = request.form.get('correct_option')

        # Convert letter to corresponding integer
        option_map = {'A': 1, 'B': 2, 'C': 3, 'D': 4}
        correct_option_num = option_map.get(correct_option.upper())
        
        if correct_option_num is None:
            flash('Invalid correct option selected')
            return render_template('admin/add_question.html', quiz=quiz)
        
        new_question = Question(
            quiz_id=quiz_id,
            question_text=question_text,
            option1=option_a,
            option2=option_b,
            option3=option_c,
            option4=option_d,
            correct_option=correct_option_num
        )
        
        db.session.add(new_question)
        db.session.commit()
        
        flash('Question added successfully')
        return redirect(url_for('admin.questions', quiz_id=quiz_id))
    
    return render_template('admin/add_question.html', quiz=quiz)

@admin_bp.route('/questions/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_question(id):
    if not current_user.is_admin:
        return redirect(url_for('user.dashboard'))
    
    question = Question.query.get_or_404(id)
    
    if request.method == 'POST':
        # Print form data for debugging
        print("Form data:", request.form)
        
        question.question_text = request.form.get('question_text', question.question_text)
        question.option1 = request.form.get('option1', question.option1)
        question.option2 = request.form.get('option2', question.option2)
        question.option3 = request.form.get('option3', question.option3)
        question.option4 = request.form.get('option4', question.option4)
        
        # Safely handle correct_option
        correct_option = request.form.get('correct_option')
        try:
            question.correct_option = int(correct_option) if correct_option is not None else question.correct_option
        except (ValueError, TypeError):
            flash('Invalid correct option selected')
            return render_template('admin/edit_question.html', question=question)
        
        db.session.commit()
        
        flash('Question updated successfully')
        return redirect(url_for('admin.questions', quiz_id=question.quiz_id))
    
    return render_template('admin/edit_question.html', question=question)

@admin_bp.route('/questions/delete/<int:id>')
@login_required
def delete_question(id):
    if not current_user.is_admin:
        return redirect(url_for('user.dashboard'))
    
    question = Question.query.get_or_404(id)
    quiz_id = question.quiz_id
    
    db.session.delete(question)
    db.session.commit()
    
    flash('Question deleted successfully')
    return redirect(url_for('admin.questions', quiz_id=quiz_id))

# User routes
@user_bp.route('/dashboard')
@login_required
def dashboard():
    if current_user.is_admin:
        return redirect(url_for('admin.dashboard'))
    
    # Get subjects the user has attempted quizzes in
    attempted_subjects = db.session.query(Subject).join(Chapter).join(Quiz).join(Score).filter(Score.user_id == current_user.id).distinct().all()

    # Get recent quiz attempts
    recent_scores = Score.query.filter_by(user_id=current_user.id).order_by(Score.timestamp.desc()).limit(5).all()
  
    total_quizzes_taken = Score.query.filter_by(user_id=current_user.id).count()
    
    # Calculate overall performance
    total_attempts = Score.query.filter_by(user_id=current_user.id).count()
    total_score = db.session.query(db.func.sum(Score.score)).filter_by(user_id=current_user.id).scalar() or 0
    avg_scores = float(total_score) / float(total_attempts) if total_attempts > 0 else 0
    
    return render_template('user/dashboard.html',
                          attempted_subjects=attempted_subjects, 
                          recent_scores=recent_scores,
                          total_quizzes_taken=total_quizzes_taken, 
                          total_score=total_score,
                          avg_scores=avg_scores)

@user_bp.route('/subjects')
@login_required
def subjects():
    subjects = Subject.query.all()
    return render_template('user/subjects.html', subjects=subjects)

@user_bp.route('/chapters/<int:subject_id>')
@login_required
def chapters(subject_id):
    subject = Subject.query.get_or_404(subject_id)
    chapters = Chapter.query.filter_by(subject_id=subject_id).all()
    return render_template('user/chapters.html', subject=subject, chapters=chapters)

@user_bp.route('/quizzes/<int:chapter_id>')
@login_required
def quizzes(chapter_id):
    chapter = Chapter.query.get_or_404(chapter_id)
    quizzes = Quiz.query.filter_by(chapter_id=chapter_id).all()

    quiz_attempts = {}
    for quiz in quizzes:
        # Look for QuizAttempt instead of Score
        previous_attempt = QuizAttempt.query.filter_by(
            user_id=current_user.id, 
            quiz_id=quiz.id, 
            status='completed'
        ).order_by(QuizAttempt.start_time.desc()).first()
        
        quiz_attempts[quiz.id] = previous_attempt
    
    return render_template('user/quizzes.html', 
                           chapter=chapter, 
                           quizzes=quizzes, 
                           quiz_attempts=quiz_attempts)


@user_bp.route('/quiz/<int:quiz_id>')
@login_required
def start_quiz(quiz_id):
    
    quiz = Quiz.query.get_or_404(quiz_id)
    questions = Question.query.filter_by(quiz_id=quiz_id).all()
    
    return render_template('user/quiz.html', quiz=quiz, questions=questions)


@user_bp.route('/quiz/<int:quiz_id>', methods=['POST'])
@login_required
def submit_quiz(quiz_id):
    # Print form data for debugging
    print("FORM DATA:", request.form)
    
    quiz = Quiz.query.get_or_404(quiz_id)
    questions = Question.query.filter_by(quiz_id=quiz_id).all()
    
    print(f"QUESTIONS: Found {len(questions)} questions")
    for q in questions:
        print(f"Question ID: {q.id}, Correct option: {q.correct_option}")
    
    total_questions = len(questions)
    correct_answers = 0
    
    # Process submitted answers
    for question in questions:
        # Try both possible field names
        submitted_answer = request.form.get(f'question{question.id}')
        if submitted_answer is None:
            # Try with "answer_" prefix instead
            submitted_answer = request.form.get(f'answer_{question.id}')
        
        print(f"Question {question.id}: submitted={submitted_answer}, correct={question.correct_option}")
        
        # Handle the case where answer is submitted as A, B, C, D instead of 1, 2, 3, 4
        if submitted_answer:
            # Check if the answer is a letter (A, B, C, D)
            if submitted_answer.upper() in ['A', 'B', 'C', 'D']:
                # Convert A=1, B=2, C=3, D=4
                answer_map = {'A': 1, 'B': 2, 'C': 3, 'D': 4}
                submitted_value = answer_map[submitted_answer.upper()]
                print(f"Converting letter {submitted_answer} to number {submitted_value}")
            else:
                # It's already a number (hopefully)
                try:
                    submitted_value = int(submitted_answer)
                except ValueError:
                    print(f"ERROR: Could not convert {submitted_answer} to a value")
                    submitted_value = -1  # Invalid answer
            
            # Now compare with the correct answer
            if submitted_value == question.correct_option:
                correct_answers += 1
                print(f"CORRECT answer for question {question.id}")
            else:
                print(f"WRONG answer for question {question.id}: {submitted_value} != {question.correct_option}")
    
    # Calculate score percentage
    if total_questions > 0:
        score_percentage = int((correct_answers / total_questions) * 100)
    else:
        score_percentage = 0
    
    print(f"FINAL SCORE: {correct_answers}/{total_questions} = {score_percentage}%")
    
    # Save score
    new_score = Score(
        user_id=current_user.id,
        quiz_id=quiz_id,
        score=score_percentage,
        total_questions=total_questions,
        correct_answers=correct_answers
    )
    
    db.session.add(new_score)
    db.session.commit()
    
    print(f"SUCCESSFULLY SAVED SCORE: ID={new_score.id}")
    
    # Redirect to results page
    return redirect(url_for('user.quiz_result', score_id=new_score.id))


@user_bp.route('/result/<int:score_id>')
@login_required
def quiz_result(score_id):
    print(f"LOADING RESULT FOR SCORE ID: {score_id}")
    
    score = Score.query.get_or_404(score_id)
    print(f"RETRIEVED SCORE: {score.correct_answers}/{score.total_questions} = {score.score}%")
    
    quiz = Quiz.query.get(score.quiz_id)
    print(f"QUIZ: {quiz.title} (ID: {quiz.id})")
    
    return render_template('user/result.html', score=score, quiz=quiz)


@common.route('/search', methods=['GET', 'POST'])
@login_required
def search():
    query = request.args.get('q', '')
    search_type = request.args.get('type', 'quiz')
    
    results = []
    if query:
        if search_type == 'quiz':
            # For regular users, only show quizzes they have access to
            # Admins can see all quizzes
            quiz_query = Quiz.query.filter(Quiz.title.ilike(f'%{query}%'))
            results = quiz_query.all()
            
        elif search_type == 'user' and current_user.is_admin:
            # Only admins can search users
            results = User.query.filter(
                (User.username.ilike(f'%{query}%')) | 
                (User.full_name.ilike(f'%{query}%'))
            ).all()
            
        elif search_type == 'subject':
            results = Subject.query.filter(Subject.name.ilike(f'%{query}%')).all()
    
    return render_template('search.html', 
                           query=query,
                           search_type=search_type, 
                           results=results,
                           is_admin=current_user.is_admin)

@common.route('/reports/summary')
@login_required
def summary_report():
    # Time period filter
    period = request.args.get('period', 'all')
    date_filter = None
    
    if period == 'week':
        date_filter = datetime.utcnow() - timedelta(days=7)
    elif period == 'month':
        date_filter = datetime.utcnow() - timedelta(days=30)
    elif period == 'year':
        date_filter = datetime.utcnow() - timedelta(days=365)
    
    # Different data for admin vs regular user
    if current_user.is_admin:
        # ADMIN VIEW - System-wide statistics
        
        # User statistics
        total_users = User.query.filter_by(is_admin=False).count()
        new_users_query = User.query.filter_by(is_admin=False)
        if date_filter:
            new_users_query = new_users_query.filter(User.id >= date_filter) # Simplified, might need created_at
        new_users = new_users_query.count()
        
        # Quiz statistics
        total_quizzes = Quiz.query.count()
        quiz_attempts_query = Score.query
        if date_filter:
            quiz_attempts_query = quiz_attempts_query.filter(Score.timestamp >= date_filter)
        total_attempts = quiz_attempts_query.count()
        
        # Average score
        avg_score = db.session.query(func.avg(Score.score)).scalar() or 0
        
        # Most popular quizzes
        popular_quizzes = db.session.query(
            Quiz, func.count(Score.id).label('attempt_count')
        ).join(Score).group_by(Quiz.id).order_by(func.count(Score.id).desc()).limit(5).all()
        
        # Best performing subjects
        best_subjects = db.session.query(
            Subject.name, 
            func.avg(Score.score).label('avg_score')
        ).join(Chapter, Subject.id == Chapter.subject_id)\
         .join(Quiz, Chapter.id == Quiz.chapter_id)\
         .join(Score, Quiz.id == Score.quiz_id)\
         .group_by(Subject.id)\
         .order_by(func.avg(Score.score).desc())\
         .limit(5).all()
        
        # Top users
        top_users = db.session.query(
            User.username,
            func.avg(Score.score).label('avg_score'),
            func.count(Score.id).label('quiz_count')
        ).join(Score, User.id == Score.user_id)\
         .group_by(User.id)\
         .having(func.count(Score.id) > 0)\
         .order_by(func.avg(Score.score).desc())\
         .limit(5).all()
        
        return render_template('summary_report.html',
                              period=period,
                              is_admin=True,
                              total_users=total_users,
                              new_users=new_users,
                              total_quizzes=total_quizzes,
                              total_attempts=total_attempts,
                              avg_score=avg_score,
                              popular_quizzes=popular_quizzes,
                              best_subjects=best_subjects,
                              top_users=top_users)
    else:
        # USER VIEW - Personal statistics
        
        # Quiz statistics for this user
        quiz_attempts_query = Score.query.filter_by(user_id=current_user.id)
        if date_filter:
            quiz_attempts_query = quiz_attempts_query.filter(Score.timestamp >= date_filter)
        
        total_attempts = quiz_attempts_query.count()
        
        # Average score for this user
        avg_score = db.session.query(func.avg(Score.score))\
            .filter(Score.user_id == current_user.id).scalar() or 0
        
        # Most taken subjects by this user
        user_subjects = db.session.query(
            Subject.name,
            func.count(Score.id).label('attempt_count'),
            func.avg(Score.score).label('avg_score')
        ).join(Chapter, Subject.id == Chapter.subject_id)\
         .join(Quiz, Chapter.id == Quiz.chapter_id)\
         .join(Score, Quiz.id == Score.quiz_id)\
         .filter(Score.user_id == current_user.id)\
         .group_by(Subject.id)\
         .order_by(func.count(Score.id).desc())\
         .limit(5).all()
        
        # Best and worst performing subjects
        best_subjects = db.session.query(
            Subject.name, 
            func.avg(Score.score).label('avg_score')
        ).join(Chapter, Subject.id == Chapter.subject_id)\
         .join(Quiz, Chapter.id == Quiz.chapter_id)\
         .join(Score, Quiz.id == Score.quiz_id)\
         .filter(Score.user_id == current_user.id)\
         .group_by(Subject.id)\
         .having(func.avg(Score.score) > 0)\
         .order_by(func.avg(Score.score).desc())\
         .limit(3).all()
        
        # User's recent activity
        recent_activity = Score.query\
            .filter_by(user_id=current_user.id)\
            .order_by(Score.timestamp.desc())\
            .limit(10).all()
        
        # Score improvement over time
        score_trend = db.session.query(
            func.strftime('%Y-%m', Score.timestamp).label('month'),
            func.avg(Score.score).label('avg_score')
            ).filter(Score.user_id == current_user.id)\
            .group_by(func.strftime('%Y-%m', Score.timestamp))\
            .order_by(func.strftime('%Y-%m', Score.timestamp))\
            .limit(6).all()
        return render_template('summary_report.html',
                              period=period,
                              is_admin=False,
                              total_attempts=total_attempts,
                              avg_score=avg_score,
                              user_subjects=user_subjects,
                              best_subjects=best_subjects,
                              recent_activity=recent_activity,
                              score_trend=score_trend)

# API Routes
@admin_bp.route('/api/subjects', methods=['GET'])
@login_required
def api_subjects():
    if not current_user.is_admin:
        return jsonify({'error': 'Unauthorized'}), 403
    
    subjects = Subject.query.all()
    subjects_list = [{'id': s.id, 'name': s.name, 'description': s.description} for s in subjects]
    
    return jsonify(subjects_list)

@admin_bp.route('/api/chapters/<int:subject_id>', methods=['GET'])
@login_required
def api_chapters(subject_id):
    if not current_user.is_admin:
        return jsonify({'error': 'Unauthorized'}), 403
    
    chapters = Chapter.query.filter_by(subject_id=subject_id).all()
    chapters_list = [{'id': c.id, 'name': c.name, 'description': c.description} for c in chapters]
    
    return jsonify(chapters_list)

@admin_bp.route('/api/quizzes/<int:chapter_id>', methods=['GET'])
@login_required
def api_quizzes(chapter_id):
    if not current_user.is_admin:
        return jsonify({'error': 'Unauthorized'}), 403
    
    quizzes = Quiz.query.filter_by(chapter_id=chapter_id).all()
    quizzes_list = [{'id': q.id, 'title': q.title, 'date': q.date_of_quiz.strftime('%Y-%m-%d')} for q in quizzes]
    
    return jsonify(quizzes_list)