from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify, send_file
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import pandas as pd
import os
from datetime import datetime
from datetime import timedelta
import random
import json
from sqlalchemy import func
from sqlalchemy import text
from collections import defaultdict
from io import BytesIO
from werkzeug.utils import secure_filename
import uuid

# --- 图片上传配置 ---
# 允许的扩展名
ALLOWED_IMG_EXT = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp'}
# 限制大小（字节）2MB
MAX_IMG_SIZE = 2 * 1024 * 1024

# ---- 时间工具 ----
BJ_OFFSET = timedelta(hours=8)

def to_bj(dt: datetime):
    """Convert naive UTC datetime stored in DB to Beijing time"""
    return (dt + BJ_OFFSET) if dt else dt

# Jinja 过滤器函数
def bjtime_filter(value, fmt='%Y-%m-%d %H:%M'):
    if not value:
        return ''
    return to_bj(value).strftime(fmt)

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test_system.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# 注册过滤器
app.jinja_env.filters['bjtime'] = bjtime_filter

# 数据库模型
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # 'teacher' or 'student'

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class QuestionBank(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    question_type = db.Column(db.String(20), nullable=False)  # 'single_choice', 'multiple_choice', ...
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    questions = db.relationship('Question', backref='bank', lazy=True, cascade="all, delete-orphan")

class Question(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    question_type = db.Column(db.String(20), nullable=False)
    content = db.Column(db.Text, nullable=False)
    image_path = db.Column(db.String(200))  # 题目配图
    option_a = db.Column(db.String(200))
    option_b = db.Column(db.String(200))
    option_c = db.Column(db.String(200))
    option_d = db.Column(db.String(200))
    option_e = db.Column(db.String(200))
    correct_answer = db.Column(db.String(200), nullable=False)
    score = db.Column(db.Integer, nullable=False)
    explanation = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    bank_id = db.Column(db.Integer, db.ForeignKey('question_bank.id'), nullable=False)

class Test(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    single_choice_count = db.Column(db.Integer, default=0)
    multiple_choice_count = db.Column(db.Integer, default=0)
    true_false_count = db.Column(db.Integer, default=0)
    fill_blank_count = db.Column(db.Integer, default=0)
    short_answer_count = db.Column(db.Integer, default=0)
    single_choice_score = db.Column(db.Integer, default=0)
    multiple_choice_score = db.Column(db.Integer, default=0)
    true_false_score = db.Column(db.Integer, default=0)
    fill_blank_score = db.Column(db.Integer, default=0)
    short_answer_score = db.Column(db.Integer, default=0)
    total_score = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)

    # 新增：题库选择
    single_choice_bank_id = db.Column(db.Integer)
    multiple_choice_bank_id = db.Column(db.Integer)
    true_false_bank_id = db.Column(db.Integer)
    fill_blank_bank_id = db.Column(db.Integer)
    short_answer_bank_id = db.Column(db.Integer)
    
    # 新增：是否允许学生自选测试内容
    allow_student_choice = db.Column(db.Boolean, default=False)

class TestResult(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    student_name = db.Column(db.String(100), nullable=False)
    class_number = db.Column(db.String(50), nullable=False)
    test_id = db.Column(db.Integer, db.ForeignKey('test.id'), nullable=False)
    score = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    answers = db.Column(db.Text)
    ip_address = db.Column(db.String(15), nullable=True) # Added ip_address column
    test = db.relationship('Test', backref=db.backref('results', lazy=True))

class StudentTestHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    student_name = db.Column(db.String(100), nullable=False)
    class_number = db.Column(db.String(50), nullable=False)
    test_count = db.Column(db.Integer, default=0)  # 总测试次数
    total_score = db.Column(db.Integer, default=0)  # 总分
    average_score = db.Column(db.Float, default=0.0)  # 平均分
    highest_score = db.Column(db.Integer, default=0)  # 最高分
    lowest_score = db.Column(db.Integer, default=0)  # 最低分
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# --- 新增：测试参数预设模型 ---
class TestPreset(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    # 题量
    single_choice_count = db.Column(db.Integer, default=0)
    multiple_choice_count = db.Column(db.Integer, default=0)
    true_false_count = db.Column(db.Integer, default=0)
    fill_blank_count = db.Column(db.Integer, default=0)
    short_answer_count = db.Column(db.Integer, default=0)
    # 分值
    single_choice_score = db.Column(db.Integer, default=0)
    multiple_choice_score = db.Column(db.Integer, default=0)
    true_false_score = db.Column(db.Integer, default=0)
    fill_blank_score = db.Column(db.Integer, default=0)
    short_answer_score = db.Column(db.Integer, default=0)
    # 题库ID
    single_choice_bank_id = db.Column(db.Integer)
    multiple_choice_bank_id = db.Column(db.Integer)
    true_false_bank_id = db.Column(db.Integer)
    fill_blank_bank_id = db.Column(db.Integer)
    short_answer_bank_id = db.Column(db.Integer)
    
    # 新增：是否允许学生自选测试内容
    allow_student_choice = db.Column(db.Boolean, default=False)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class ShortAnswerSubmission(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    result_id = db.Column(db.Integer, db.ForeignKey('test_result.id'), nullable=False)
    question_id = db.Column(db.Integer, db.ForeignKey('question.id'), nullable=False)
    student_answer = db.Column(db.Text, nullable=False)
    image_path = db.Column(db.String(200))
    score = db.Column(db.Integer, nullable=True)
    comment = db.Column(db.Text, nullable=True)
    graded_bool = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

def shuffle_options(question):
    """
    返回题目选项的原始顺序
    """
    return {
        'content': question.content,
        'id': question.id,
        'score': question.score,
        'option_a': question.option_a,
        'option_b': question.option_b,
        'option_c': question.option_c,
        'option_d': question.option_d,
        'correct_answer': question.correct_answer,
        'original_correct_answer': question.correct_answer
    }
# 路由
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/teacher/login', methods=['GET', 'POST'])
def teacher_login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username, role='teacher').first()
        if user and user.check_password(password):
            session['user_id'] = user.id
            session['role'] = 'teacher'
            return redirect(url_for('teacher_dashboard'))
        flash('用户名或密码错误', 'login_error')
    return render_template('teacher_login.html')

@app.route('/teacher/dashboard')
def teacher_dashboard():
    if 'role' not in session or session['role'] != 'teacher':
        return redirect(url_for('teacher_login'))
    
    # 获取最新的测试设置
    last_test = Test.query.order_by(Test.created_at.desc()).first()
    
    # 获取各类型的题目
    single_choice_questions = Question.query.filter_by(question_type='single_choice').all()
    multiple_choice_questions = Question.query.filter_by(question_type='multiple_choice').all()
    true_false_questions = Question.query.filter_by(question_type='true_false').all()
    fill_blank_questions = Question.query.filter_by(question_type='fill_blank').all()
    short_answer_questions = Question.query.filter_by(question_type='short_answer').all()
    
    return render_template('teacher_dashboard.html',
                         last_test=last_test,
                         single_choice_questions=single_choice_questions,
                         multiple_choice_questions=multiple_choice_questions,
                         true_false_questions=true_false_questions,
                         fill_blank_questions=fill_blank_questions,
                         short_answer_questions=short_answer_questions,
                         last_import_filename=session.get('last_import_filename'),
                         last_import_filepath=session.get('last_import_filepath'))

@app.route('/import_questions', methods=['POST'])
def import_questions():
    if 'role' not in session or session['role'] != 'teacher':
        return redirect(url_for('teacher_login'))
    if 'csv_file' not in request.files:
        flash('请选择文件')
        return redirect(url_for('teacher_dashboard'))
    file = request.files['csv_file']
    if file.filename == '':
        flash('请选择文件')
        return redirect(url_for('teacher_dashboard'))
    if file and (file.filename.endswith('.csv') or file.filename.endswith('.xlsx')):
        try:
            session['last_import_filename'] = file.filename
            session['last_import_filepath'] = getattr(file, 'stream', None) and getattr(file.stream, 'name', None) or ''
            question_type = request.form.get('question_type')
            bank_name = request.form.get('bank_name') or file.filename
            if not question_type:
                flash('请选择题目类型')
                return redirect(url_for('teacher_dashboard'))
            # 新建题库
            bank = QuestionBank(name=bank_name, question_type=question_type)
            db.session.add(bank)
            db.session.commit()
            # 读取文件并导入题目（与原逻辑一致，但需加bank_id）
            df = None
            if file.filename.endswith('.csv'):
                encodings = ['utf-8', 'gbk', 'gb2312', 'gb18030']
                for encoding in encodings:
                    try:
                        file.seek(0)
                        df = pd.read_csv(file, encoding=encoding)
                        break
                    except UnicodeDecodeError:
                        continue
                if df is None:
                    flash('无法读取CSV文件，请检查文件编码')
                    return redirect(url_for('teacher_dashboard'))
            elif file.filename.endswith('.xlsx'):
                try:
                    file.seek(0)
                    df = pd.read_excel(file)
                except Exception as e:
                    flash(f'无法读取Excel文件：{str(e)}')
                    return redirect(url_for('teacher_dashboard'))
            # 根据题目类型设置列名映射
            if question_type == 'single_choice':
                column_mapping = {
                    '题干': ['题干', '题目', '问题'],
                    '选项A': ['选项A', 'A选项', 'A'],
                    '选项B': ['选项B', 'B选项', 'B'],
                    '选项C': ['选项C', 'C选项', 'C'],
                    '选项D': ['选项D', 'D选项', 'D'],
                    '正确答案': ['正确答案', '答案', '正确答案选项'],
                    '分值': ['分值', '分数', '得分'],
                    '解析': ['解析', '答案解析', '解释']
                }
            elif question_type == 'multiple_choice':
                column_mapping = {
                    '题干': ['题干', '题目', '问题'],
                    '选项A': ['选项A', 'A选项', 'A'],
                    '选项B': ['选项B', 'B选项', 'B'],
                    '选项C': ['选项C', 'C选项', 'C'],
                    '选项D': ['选项D', 'D选项', 'D'],
                    '选项E': ['选项E', 'E选项', 'E'],
                    '正确答案': ['正确答案', '答案', '正确答案选项'],
                    '分值': ['分值', '分数', '得分'],
                    '解析': ['解析', '答案解析', '解释']
                }
            elif question_type == 'true_false':
                column_mapping = {
                    '题干': ['题干', '题目', '问题'],
                    '正确答案': ['正确答案', '答案', '正确答案选项'],
                    '分值': ['分值', '分数', '得分'],
                    '解析': ['解析', '答案解析', '解释']
                }
            elif question_type == 'short_answer':
                # 简答题：题目内容、学生答案可包含富文本/图片；分值和解析可选
                column_mapping = {
                    '题干': ['题目内容', '题干', '题目', '问题', '内容'],
                    '正确答案': ['学生答案', '学生答题', '参考答案', '答案'],
                    '分值': ['分值', '分数', '得分'],
                    '解析': ['解析', '答案解析', '解释']
                }
            else:  # fill_blank
                column_mapping = {
                    '题干': ['题干', '题目', '问题'],
                    '正确答案': ['正确答案', '答案', '参考答案'],
                    '分值': ['分值', '分数', '得分'],
                    '解析': ['解析', '答案解析', '解释']
                }
            # 查找实际列名
            actual_columns = {}
            for standard_name, possible_names in column_mapping.items():
                for name in possible_names:
                    if name in df.columns:
                        actual_columns[standard_name] = name
                        break
            # 检查是否找到所有必要的列
            missing_columns = [col for col in column_mapping.keys() if col not in actual_columns]
            if missing_columns:
                flash(f'CSV文件缺少必要的列：{", ".join(missing_columns)}')
                return redirect(url_for('teacher_dashboard'))
            # 导入题目
            for _, row in df.iterrows():
                question = Question(
                    question_type=question_type,
                    content=row[actual_columns['题干']],
                    option_a=row[actual_columns['选项A']] if '选项A' in actual_columns else None,
                    option_b=row[actual_columns['选项B']] if '选项B' in actual_columns else None,
                    option_c=row[actual_columns['选项C']] if '选项C' in actual_columns else None,
                    option_d=row[actual_columns['选项D']] if '选项D' in actual_columns else None,
                    option_e=row[actual_columns['选项E']] if '选项E' in actual_columns else None,
                    correct_answer=row[actual_columns['正确答案']],
                    score=int(row[actual_columns['分值']]) if '分值' in actual_columns else 0,
                    explanation=row[actual_columns['解析']] if '解析' in actual_columns else None,
                    bank_id=bank.id
                )
                db.session.add(question)
            db.session.commit()
            flash('题库导入成功')
        except Exception as e:
            flash(f'导入失败：{str(e)}')
            db.session.rollback()
    else:
        flash('请上传CSV或Excel(XLSX)文件')
    return redirect(url_for('teacher_dashboard'))

@app.route('/set_test_params', methods=['POST'])
def set_test_params():
    if 'role' not in session or session['role'] != 'teacher':
        return redirect(url_for('teacher_login'))
    try:
        # 先将所有旧测试设为不激活
        Test.query.update({'is_active': False})
        db.session.commit()
        # 计算总分
        total_score = (
            int(request.form.get('single_choice_count', 0)) * int(request.form.get('single_choice_score', 0)) +
            int(request.form.get('multiple_choice_count', 0)) * int(request.form.get('multiple_choice_score', 0)) +
            int(request.form.get('true_false_count', 0)) * int(request.form.get('true_false_score', 0)) +
            int(request.form.get('fill_blank_count', 0)) * int(request.form.get('fill_blank_score', 0)) +
            int(request.form.get('short_answer_count', 0)) * int(request.form.get('short_answer_score', 0))
        )
        test = Test(
            title=request.form.get('test_title'),
            single_choice_count=int(request.form.get('single_choice_count', 0)),
            multiple_choice_count=int(request.form.get('multiple_choice_count', 0)),
            true_false_count=int(request.form.get('true_false_count', 0)),
            fill_blank_count=int(request.form.get('fill_blank_count', 0)),
            short_answer_count=int(request.form.get('short_answer_count', 0)),
            single_choice_score=int(request.form.get('single_choice_score', 0)),
            multiple_choice_score=int(request.form.get('multiple_choice_score', 0)),
            true_false_score=int(request.form.get('true_false_score', 0)),
            fill_blank_score=int(request.form.get('fill_blank_score', 0)),
            short_answer_score=int(request.form.get('short_answer_score', 0)),
            total_score=total_score,
            is_active=True
        )
        db.session.add(test)
        db.session.commit()
        flash('测试参数设置成功')
    except Exception as e:
        flash(f'设置失败：{str(e)}')
        db.session.rollback()
    return redirect(url_for('teacher_dashboard'))

@app.route('/student/start', methods=['GET', 'POST'])
def student_start():
    if request.method == 'POST':
        name = request.form.get('name')
        class_number = request.form.get('class_number')
        test_content = request.form.get('test_content')  # 新增：获取学生选择的测试内容
        
        if not name or not class_number:
            flash('姓名和班级号不能为空')
            return render_template('student_start.html')
        
        username = f"{name}_{class_number}"
        student = User.query.filter_by(username=username, role='student').first()
        if not student:
            student = User(username=username, role='student')
            student.set_password(username)
            db.session.add(student)
            db.session.commit()
        
        session['student_id'] = student.id
        session['student_name'] = name
        session['class_number'] = class_number
        session['selected_preset_id'] = test_content if test_content else None  # 新增：存储选择的预设ID
        
        return redirect(url_for('test'))
    return render_template('student_start.html')

@app.route('/test')
def test():
    if 'student_id' not in session:
        return redirect(url_for('student_start'))
    
    # 获取学生选择的预设ID
    selected_preset_id = session.get('selected_preset_id')
    
    # 根据选择决定使用哪个测试配置
    if selected_preset_id:
        # 学生选择了预设，使用预设配置
        preset = TestPreset.query.get(selected_preset_id)
        if not preset:
            flash('选择的测试内容不存在')
            return redirect(url_for('student_start'))
        
        # 使用预设配置创建临时测试对象
        test_config = {
            'title': preset.title,
            'single_choice_count': preset.single_choice_count or 0,
            'multiple_choice_count': preset.multiple_choice_count or 0,
            'true_false_count': preset.true_false_count or 0,
            'fill_blank_count': preset.fill_blank_count or 0,
            'short_answer_count': preset.short_answer_count or 0,
            'single_choice_score': preset.single_choice_score or 0,
            'multiple_choice_score': preset.multiple_choice_score or 0,
            'true_false_score': preset.true_false_score or 0,
            'fill_blank_score': preset.fill_blank_score or 0,
            'short_answer_score': preset.short_answer_score or 0,
            'single_choice_bank_id': preset.single_choice_bank_id,
            'multiple_choice_bank_id': preset.multiple_choice_bank_id,
            'true_false_bank_id': preset.true_false_bank_id,
            'fill_blank_bank_id': preset.fill_blank_bank_id,
            'short_answer_bank_id': preset.short_answer_bank_id,
            'total_score': ((preset.single_choice_count or 0) * (preset.single_choice_score or 0) +
                          (preset.multiple_choice_count or 0) * (preset.multiple_choice_score or 0) +
                          (preset.true_false_count or 0) * (preset.true_false_score or 0) +
                          (preset.fill_blank_count or 0) * (preset.fill_blank_score or 0) +
                          (preset.short_answer_count or 0) * (preset.short_answer_score or 0))
        }
    else:
        # 学生没有选择，使用当前激活的测试
        current_test = Test.query.filter_by(is_active=True).first()
        if not current_test:
            # 如果没有激活的测试，尝试获取最新的测试
            current_test = Test.query.order_by(Test.created_at.desc()).first()
            
        if not current_test:
            flash('当前没有可用的测试，请联系教师')
            return redirect(url_for('student_start'))
        
        # 确保所有必要的字段都有默认值
        test_config = {
            'title': current_test.title or '默认测试',
            'single_choice_count': current_test.single_choice_count or 0,
            'multiple_choice_count': current_test.multiple_choice_count or 0,
            'true_false_count': current_test.true_false_count or 0,
            'fill_blank_count': current_test.fill_blank_count or 0,
            'short_answer_count': current_test.short_answer_count or 0,
            'single_choice_score': current_test.single_choice_score or 0,
            'multiple_choice_score': current_test.multiple_choice_score or 0,
            'true_false_score': current_test.true_false_score or 0,
            'fill_blank_score': current_test.fill_blank_score or 0,
            'short_answer_score': current_test.short_answer_score or 0,
            'single_choice_bank_id': current_test.single_choice_bank_id,
            'multiple_choice_bank_id': current_test.multiple_choice_bank_id,
            'true_false_bank_id': current_test.true_false_bank_id,
            'fill_blank_bank_id': current_test.fill_blank_bank_id,
            'short_answer_bank_id': current_test.short_answer_bank_id,
            'total_score': current_test.total_score or 0
        }
    
    # 每次都重新抽题，不再判断是否已参加过
    def pick_questions(q_type, count, bank_id):
        if count <= 0:
            return []
        q = Question.query.filter_by(question_type=q_type)
        if bank_id:
            q = q.filter_by(bank_id=bank_id)
        return q.order_by(func.random()).limit(count).all()

    single_choice_questions  = pick_questions('single_choice',  test_config['single_choice_count'],  test_config['single_choice_bank_id'])
    multiple_choice_questions = pick_questions('multiple_choice', test_config['multiple_choice_count'], test_config['multiple_choice_bank_id'])
    true_false_questions      = pick_questions('true_false',   test_config['true_false_count'],     test_config['true_false_bank_id'])
    fill_blank_questions      = pick_questions('fill_blank',   test_config['fill_blank_count'],     test_config['fill_blank_bank_id'])
    short_answer_questions    = pick_questions('short_answer', test_config['short_answer_count'],   test_config['short_answer_bank_id'])
    
    return render_template('test.html', 
                         test=test_config,
                         single_choice_questions=single_choice_questions,
                         multiple_choice_questions=multiple_choice_questions,
                         true_false_questions=true_false_questions,
                         fill_blank_questions=fill_blank_questions,
                         short_answer_questions=short_answer_questions)

@app.route('/submit_test', methods=['POST'])
def submit_test():
    if 'student_id' not in session:
        return redirect(url_for('student_start'))
    
    # 获取学生选择的预设ID
    selected_preset_id = session.get('selected_preset_id')
    
    # 根据选择决定使用哪个测试配置
    if selected_preset_id:
        # 学生选择了预设，使用预设配置
        preset = TestPreset.query.get(selected_preset_id)
        if not preset:
            flash('选择的测试内容不存在')
            return redirect(url_for('student_start'))
        
        # 使用预设配置创建临时测试对象
        test_config = {
            'single_choice_score': preset.single_choice_score,
            'multiple_choice_score': preset.multiple_choice_score,
            'true_false_score': preset.true_false_score,
            'fill_blank_score': preset.fill_blank_score,
            'short_answer_score': preset.short_answer_score
        }
    else:
        # 学生没有选择，使用当前激活的测试
        current_test = Test.query.filter_by(is_active=True).first()
        if not current_test:
            flash('当前没有进行中的测试')
            return redirect(url_for('student_dashboard'))
        test_config = current_test
        
    # 获取所有答案
    answers = {}
    for key in request.form:
        if key.startswith('answer_'):
            question_id = int(key.split('_')[1])
            values = request.form.getlist(key)
            if len(values) == 1:
                answers[question_id] = values[0].strip().upper()
            else:
                # 多选题，拼接为逗号分隔的大写字母，顺序统一
                answers[question_id] = ','.join(sorted([v.strip().upper() for v in values if v.strip()]))
    
    # 计算得分
    total_score = 0
    for question_id, answer in answers.items():
        question = Question.query.get(question_id)
        if not question:
            continue
        if question.question_type == 'single_choice':
            if answer == question.correct_answer:
                # 处理test_config可能是字典或对象的情况
                score = test_config.get('single_choice_score') if isinstance(test_config, dict) else test_config.single_choice_score
                total_score += score or 0
        elif question.question_type == 'multiple_choice':
            def normalize(ans):
                return ''.join(sorted([c for c in ans.replace(',', '').replace(' ', '').upper() if c in 'ABCDE']))
            is_correct = normalize(answer) == normalize(question.correct_answer)
            if is_correct:
                score = test_config.get('multiple_choice_score') if isinstance(test_config, dict) else test_config.multiple_choice_score
                total_score += score or 0
        elif question.question_type == 'true_false':
            if answer == question.correct_answer:
                score = test_config.get('true_false_score') if isinstance(test_config, dict) else test_config.true_false_score
                total_score += score or 0
        elif question.question_type == 'fill_blank':
            # 处理填空题多个答案
            correct_fill_ins = [f.strip().lower() for f in question.correct_answer.split('、') if f.strip()]
            num_fill_ins = len(correct_fill_ins)
            if num_fill_ins > 0:
                score = test_config.get('fill_blank_score') if isinstance(test_config, dict) else test_config.fill_blank_score
                score_per_fill_in = round((score or 0) / num_fill_ins, 1)
                fill_blank_score = 0
                student_fill_ins = []
                for i in range(1, 5): # 假设最多4个填空输入框
                    student_answer = request.form.get(f'answer_{question_id}_{i}', '').strip().lower()
                    student_fill_ins.append(student_answer)
                    if i <= num_fill_ins and student_answer == correct_fill_ins[i-1]:
                        fill_blank_score += score_per_fill_in
                total_score += fill_blank_score
                # 将学生填空答案存入answers字典，以便test_result页显示
                cleaned = [s.strip() for s in student_fill_ins if s.strip()]
                answers[question_id] = '、'.join(cleaned)
            else:
                # 如果正确答案格式错误或为空，该题不得分，学生答案也记录
                student_fill_ins = []
                for i in range(1, 5):
                    student_fill_ins.append(request.form.get(f'answer_{question_id}_{i}', '').strip().lower())
                cleaned = [s.strip() for s in student_fill_ins if s.strip()]
                answers[question_id] = '、'.join(cleaned)
        elif question.question_type == 'short_answer':
            student_answer = request.form.get(f'answer_{question_id}', '').strip()
            img_url = request.form.get(f'answer_{question_id}_img_url', '').strip()
            # 暂时保存简答题信息，稍后创建记录
            short_answer_data = {
                'question_id': question_id,
                'student_answer': student_answer,
                'image_path': img_url
            }
            # 将简答题数据添加到answers字典中
            answers[question_id] = student_answer
    # 题目循环结束后，只插入一次TestResult
    ip_addr = request.headers.get('X-Forwarded-For', request.remote_addr)
    
    # 确定test_id
    if selected_preset_id:
        # 使用预设时，需要创建一个特殊的测试记录
        preset = TestPreset.query.get(selected_preset_id)
        if preset:
            try:
                # 创建一个临时的测试记录用于关联
                temp_test = Test(
                    title=f"预设测试: {preset.title}",
                    single_choice_count=preset.single_choice_count or 0,
                    multiple_choice_count=preset.multiple_choice_count or 0,
                    true_false_count=preset.true_false_count or 0,
                    fill_blank_count=preset.fill_blank_count or 0,
                    short_answer_count=preset.short_answer_count or 0,
                    single_choice_score=preset.single_choice_score or 0,
                    multiple_choice_score=preset.multiple_choice_score or 0,
                    true_false_score=preset.true_false_score or 0,
                    fill_blank_score=preset.fill_blank_score or 0,
                    short_answer_score=preset.short_answer_score or 0,
                    total_score=((preset.single_choice_count or 0) * (preset.single_choice_score or 0) +
                               (preset.multiple_choice_count or 0) * (preset.multiple_choice_score or 0) +
                               (preset.true_false_count or 0) * (preset.true_false_score or 0) +
                               (preset.fill_blank_count or 0) * (preset.fill_blank_score or 0) +
                               (preset.short_answer_count or 0) * (preset.short_answer_score or 0)),
                    single_choice_bank_id=preset.single_choice_bank_id,
                    multiple_choice_bank_id=preset.multiple_choice_bank_id,
                    true_false_bank_id=preset.true_false_bank_id,
                    fill_blank_bank_id=preset.fill_blank_bank_id,
                    short_answer_bank_id=preset.short_answer_bank_id,
                    is_active=False  # 标记为非活跃，避免影响正常测试
                )
                db.session.add(temp_test)
                db.session.flush()  # 获取ID但不提交
                test_id = temp_test.id
            except Exception as e:
                # 如果创建临时测试失败，记录错误并重定向
                print(f"创建临时测试失败: {e}")
                flash('创建测试记录失败，请重试')
                return redirect(url_for('student_start'))
        else:
            flash('选择的测试内容不存在')
            return redirect(url_for('student_start'))
    else:
        # 使用默认测试时，test_id为当前测试的ID
        if isinstance(test_config, dict):
            # 如果是字典格式，需要从数据库重新获取Test对象
            current_test = Test.query.filter_by(is_active=True).first()
            if not current_test:
                current_test = Test.query.order_by(Test.created_at.desc()).first()
            test_id = current_test.id if current_test else None
        else:
            # 如果是对象格式，直接获取ID
            test_id = test_config.id
    
    # 确保test_id不为None
    if test_id is None:
        flash('无法获取测试ID，请重试')
        return redirect(url_for('student_start'))
    
    result = TestResult(
        student_id=session['student_id'],
        student_name=session.get('student_name', ''),
        class_number=session.get('class_number', ''),
        test_id=test_id,
        score=total_score,
        answers=json.dumps(answers),
        ip_address=ip_addr
    )
    db.session.add(result)
    db.session.commit()  # 先提交，确保TestResult有数据

    # 现在创建简答题提交记录，此时result.id已经可用
    for question_id, answer in answers.items():
        question = Question.query.get(question_id)
        if question and question.question_type == 'short_answer':
            # 从answers中获取简答题的图片路径信息
            img_url = request.form.get(f'answer_{question_id}_img_url', '').strip()
            sa = ShortAnswerSubmission(
                result_id=result.id,  # 现在可以使用result.id
                question_id=question_id,
                student_answer=answer,
                image_path=img_url
            )
            db.session.add(sa)
    
    db.session.commit()

    # 统计历史
    all_results = TestResult.query.filter_by(student_id=session['student_id']).all()
    test_count = len(all_results)
    total_score_sum = sum(r.score for r in all_results)
    average_score = total_score_sum / test_count if test_count > 0 else 0
    highest_score = max((r.score for r in all_results), default=0)
    lowest_score = min((r.score for r in all_results), default=0)

    history = StudentTestHistory.query.filter_by(student_id=session['student_id']).first()
    if not history:
        history = StudentTestHistory(
            student_id=session['student_id'],
            student_name=session.get('student_name', ''),
            class_number=session.get('class_number', ''),
        )
        db.session.add(history)

    history.test_count = test_count
    history.total_score = total_score_sum
    history.average_score = average_score
    history.highest_score = highest_score
    history.lowest_score = lowest_score

    db.session.commit()
        
    flash('测试提交成功！')
    
    return redirect(url_for('student_dashboard'))

@app.route('/api/question/<int:question_id>', methods=['GET'])
def get_question_api(question_id):
    if 'role' not in session or session['role'] != 'teacher':
        return jsonify({'error': 'Unauthorized'}), 401
    
    question = Question.query.get_or_404(question_id)
    return jsonify({
        'id': question.id,
        'content': question.content,
        'option_a': question.option_a,
        'option_b': question.option_b,
        'option_c': question.option_c,
        'option_d': question.option_d,
        'correct_answer': question.correct_answer,
        'score': question.score,
        'question_type': question.question_type
    })

@app.route('/api/question/<question_id>', methods=['POST', 'DELETE'])
def manage_question(question_id):
    if 'role' not in session or session['role'] != 'teacher':
        return jsonify({'error': 'Unauthorized'}), 401
    
    if request.method == 'DELETE':
        question = Question.query.get_or_404(question_id)
        db.session.delete(question)
        db.session.commit()
        return jsonify({'success': True})
    
    # POST method - create or update question
    form = request.form
    if question_id == 'new':
        question = Question()
        question.bank_id = form.get('bank_id', type=int)
        question.question_type = form.get('question_type')
        db.session.add(question)
    else:
        question = Question.query.get_or_404(question_id)
    
    question.content = form.get('content')
    question.correct_answer = form.get('correct_answer')
    question.score = form.get('score')
    if form.get('image_path') is not None:
        question.image_path = form.get('image_path')
    
    if question.question_type in ['single_choice', 'multiple_choice']:
        question.option_a = form.get('option_a')
        question.option_b = form.get('option_b')
        question.option_c = form.get('option_c')
        question.option_d = form.get('option_d')
    
    db.session.commit()
    return jsonify({'success': True})

@app.route('/edit_question', methods=['POST'])
def edit_question():
    if 'role' not in session or session['role'] != 'teacher':
        flash('未授权')
        return redirect(url_for('teacher_login'))
    try:
        question_id = request.form.get('question_id')
        if not question_id:
            flash('题目ID不能为空')
            return redirect(url_for('teacher_dashboard'))
        question = Question.query.get_or_404(question_id)

        # 始终更新题干内容
        content = request.form.get('content')
        if content is not None:
            question.content = content

        question_type = request.form.get('question_type')
        if question_type:
            question.question_type = question_type
        try:
            score = int(request.form.get('score', 0))
            if score > 0:
                question.score = score
        except ValueError:
            flash('分值必须是整数')
            return redirect(url_for('teacher_dashboard'))
        question.explanation = request.form.get('explanation', '')
        if question_type in ['single_choice', 'multiple_choice']:
            question.option_a = request.form.get('option_a', '')
            question.option_b = request.form.get('option_b', '')
            question.option_c = request.form.get('option_c', '')
            question.option_d = request.form.get('option_d', '')
            question.option_e = request.form.get('option_e', '') if question_type == 'multiple_choice' else None
            if request.form.get('correct_answer'):
                question.correct_answer = request.form.get('correct_answer').upper()
        elif question_type == 'true_false':
            if request.form.get('correct_answer'):
                question.correct_answer = request.form.get('correct_answer')
        else:
            if request.form.get('correct_answer'):
                question.correct_answer = request.form.get('correct_answer')
        db.session.commit()
        flash('题目修改成功')
    except Exception as e:
        db.session.rollback()
        flash(f'修改失败：{str(e)}')
    return redirect(url_for('teacher_dashboard'))

@app.route('/change_password', methods=['POST'])
def change_password():
    if 'role' not in session or session['role'] != 'teacher':
        flash('未授权')
        return redirect(url_for('teacher_login'))
    
    if 'user_id' not in session:
        flash('请先登录')
        return redirect(url_for('teacher_login'))
    
    user = User.query.get(session['user_id'])
    if not user:
        flash('用户不存在')
        return redirect(url_for('teacher_login'))
    
    current_password = request.form.get('current_password')
    new_password = request.form.get('new_password')
    confirm_password = request.form.get('confirm_password')
    
    # 验证当前密码是否正确
    if not user.check_password(current_password):
        flash('当前密码错误')
        return redirect(url_for('teacher_dashboard'))
    
    # 验证新密码
    if new_password != confirm_password:
        flash('两次输入的新密码不一致')
        return redirect(url_for('teacher_dashboard'))
    
    # 更新密码
    try:
        user.set_password(new_password)
        db.session.commit()
        flash('密码修改成功')
    except Exception as e:
        db.session.rollback()
        flash(f'密码修改失败：{str(e)}')
    
    return redirect(url_for('teacher_dashboard'))

@app.route('/test_statistics')
def test_statistics():
    if 'role' not in session or session['role'] != 'teacher':
        return redirect(url_for('teacher_login'))
    # 获取所有考试及人次
    tests = Test.query.order_by(Test.created_at.desc()).all()
    data = []
    for t in tests:
        cnt = TestResult.query.filter_by(test_id=t.id).count()
        data.append({'test': t, 'count': cnt})
    return render_template('test_statistics.html', tests=data) 

@app.route('/delete_test/<int:test_id>', methods=['POST'])
def delete_test(test_id):
    if 'role' not in session or session['role'] != 'teacher':
        return redirect(url_for('teacher_login'))
    try:
        TestResult.query.filter_by(test_id=test_id).delete()
        Test.query.filter_by(id=test_id).delete()
        db.session.commit()
        flash('测试删除成功')
    except Exception as e:
        db.session.rollback()
        flash(f'删除失败：{e}')
    return redirect(url_for('test_statistics'))

@app.route('/test_statistics/<int:test_id>')
def get_test_statistics(test_id):
    if 'role' not in session or session['role'] != 'teacher':
        return redirect(url_for('teacher_login'))
    # 获取指定考试的所有成绩
    results = TestResult.query.filter_by(test_id=test_id).order_by(TestResult.class_number, TestResult.student_name, TestResult.created_at).all()
    # 按班级分组统计
    class_stats = {}
    class_students = {}
    for result in results:
        # 统计数据
        if result.class_number not in class_stats:
            class_stats[result.class_number] = {
                'student_count': 0,
                'total_score': 0,
                'scores': [],
                'pass_count': 0
            }
        stats = class_stats[result.class_number]
        stats['student_count'] += 1
        stats['total_score'] += result.score
        stats['scores'].append(result.score)
        if result.score >= 60:
            stats['pass_count'] += 1
        # 学生成绩明细
        if result.class_number not in class_students:
            class_students[result.class_number] = []
        class_students[result.class_number].append({
            'name': result.student_name,
            'score': result.score,
            'submit_time': to_bj(result.created_at).strftime('%Y-%m-%d %H:%M:%S'),
            'ip': result.ip_address,
            'result_id': result.id
        })
    # 计算每个班级的统计数据
    statistics = []
    for class_number, stats in class_stats.items():
        if stats['student_count'] > 0:
            statistics.append({
                'class_number': class_number,
                'student_count': stats['student_count'],
                'average_score': stats['total_score'] / stats['student_count'],
                'max_score': max(stats['scores']),
                'min_score': min(stats['scores']),
                'pass_rate': stats['pass_count'] / stats['student_count']
            })
    statistics.sort(key=lambda x: x['class_number'])
    # 按班级号排序
    class_students = dict(sorted(class_students.items(), key=lambda x: x[0]))
    # 统计每道题的错误率
    question_stats = defaultdict(lambda: {'total': 0, 'wrong': 0, 'content': '', 'question_type': '', 'correct_answer': ''})
    for result in results:
        answers = json.loads(result.answers)
        for qid_str, stu_ans in answers.items():
            qid = int(qid_str)
            question = Question.query.get(qid)
            if not question:
                continue
            question_stats[qid]['total'] += 1
            question_stats[qid]['content'] = question.content
            question_stats[qid]['question_type'] = question.question_type
            question_stats[qid]['correct_answer'] = question.correct_answer
            # 判定正误（与 test_result 逻辑一致）
            is_wrong = False
            if question.question_type == 'single_choice':
                is_wrong = stu_ans != question.correct_answer
            elif question.question_type == 'multiple_choice':
                def normalize(ans):
                    return ''.join(sorted([c for c in ans.replace(',', '').replace(' ', '').upper() if c in 'ABCDE']))
                is_wrong = normalize(stu_ans) != normalize(question.correct_answer)
            elif question.question_type == 'true_false':
                is_wrong = stu_ans != question.correct_answer
            elif question.question_type == 'fill_blank':
                def norm_fill(s):
                    parts = [p.strip().lower() for p in s.replace('、', ',').split(',') if p.strip()]
                    return ','.join(parts)
                is_wrong = norm_fill(stu_ans) != norm_fill(question.correct_answer)
            # 简答题暂不统计
            if is_wrong:
                question_stats[qid]['wrong'] += 1
    # 计算错误率并排序
    error_questions = []
    for qid, stat in question_stats.items():
        if stat['total'] > 0:
            error_rate = stat['wrong'] / stat['total']
            question = Question.query.get(qid) # 重新获取question对象以访问选项
            if question:
                q_data = {
                    'id': qid,
                    'content': stat['content'],
                    'question_type': stat['question_type'],
                    'correct_answer': stat['correct_answer'],
                    'error_rate': error_rate,
                    'wrong_count': stat['wrong'],
                    'total_count': stat['total']
                }
                if question.question_type in ['single_choice', 'multiple_choice']:
                    q_data['option_a'] = question.option_a
                    q_data['option_b'] = question.option_b
                    q_data['option_c'] = question.option_c
                    q_data['option_d'] = question.option_d
                    if question.question_type == 'multiple_choice':
                        q_data['option_e'] = question.option_e
                error_questions.append(q_data)
    error_questions.sort(key=lambda x: x['error_rate'], reverse=True)
    top_error_questions = error_questions[:10]
    return render_template('test_statistics_detail.html', statistics=statistics, class_students=class_students, top_error_questions=top_error_questions)

@app.route('/test_statistics/<int:test_id>/students')
def get_test_students(test_id):
    if 'role' not in session or session['role'] != 'teacher':
        return jsonify({'error': '未授权'}), 401
    
    # 获取指定考试的所有成绩
    results = TestResult.query.filter_by(test_id=test_id).order_by(TestResult.class_number, TestResult.student_name).all()
    
    # 按班级分组
    class_groups = {}
    for result in results:
        if result.class_number not in class_groups:
            class_groups[result.class_number] = []
        
        class_groups[result.class_number].append({
            'name': result.student_name,
            'score': result.score,
            'submit_time': to_bj(result.created_at).strftime('%Y-%m-%d %H:%M:%S'),
            'ip': result.ip_address
        })
    
    # 转换为列表格式
    statistics = []
    for class_number, students in sorted(class_groups.items()):
        statistics.append({
            'class_number': class_number,
            'students': sorted(students, key=lambda x: (-x['score'], x['name']))  # 按分数降序，姓名升序排序
        })
    
    return jsonify(statistics)

@app.route('/initialize_data', methods=['POST'])
def initialize_data():
    if 'role' not in session or session['role'] != 'teacher':
        return jsonify({'success': False, 'message': '未授权'}), 401
    
    try:
        # 清除所有测试相关数据
        TestResult.query.delete()
        StudentTestHistory.query.delete()
        Test.query.delete()
        Question.query.delete()
        
        # 提交更改
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '数据初始化成功'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'初始化失败：{str(e)}'
        })

@app.route('/clear_questions/<question_type>', methods=['POST'])
def clear_questions(question_type):
    if 'role' not in session or session['role'] != 'teacher':
        return jsonify({'success': False, 'message': '未授权'}), 401
    
    try:
        Question.query.filter_by(question_type=question_type).delete()
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)})

@app.route('/test_result/<int:result_id>')
def test_result(result_id):
    # 获取测试结果
    result = TestResult.query.get_or_404(result_id)
    
    # 检查权限：学生只能查看自己的，教师可以查看所有
    if 'role' not in session:
        return redirect(url_for('student_start'))
    
    if session.get('role') == 'teacher':
        # 教师可以查看所有学生的答题详情
        pass
    elif session.get('role') == 'student':
        # 学生只能查看自己的
        if 'student_id' not in session or result.student_id != session['student_id']:
            flash('无权访问此测试结果')
            return redirect(url_for('student_dashboard'))
    else:
        flash('无权访问此测试结果')
        return redirect(url_for('student_start'))
    
    # 获取测试信息
    test = Test.query.get(result.test_id)
    
    # 获取学生信息
    if session.get('role') == 'teacher':
        # 教师查看时，从 result 中获取学生信息
        student_id = result.student_id
        student = User.query.get(student_id)
        # 教师查看时也获取学生历史记录
        history = StudentTestHistory.query.filter_by(
            student_id=student_id
        ).first()
    else:
        # 学生查看自己的
        student = User.query.get(session['student_id'])
        history = StudentTestHistory.query.filter_by(
            student_id=session['student_id']
        ).first()
    
    # 获取题目详情
    questions = []
    answers = json.loads(result.answers)
    
    for question_id, answer in answers.items():
        question = Question.query.get(int(question_id))
        if question:
            is_correct = False
            if question.question_type == 'single_choice':
                is_correct = answer == question.correct_answer
                score = test.single_choice_score if is_correct else 0
            elif question.question_type == 'multiple_choice':
                def normalize(ans):
                    return ''.join(sorted([c for c in ans.replace(',', '').replace(' ', '').upper() if c in 'ABCDE']))
                is_correct = normalize(answer) == normalize(question.correct_answer)
                score = test.multiple_choice_score if is_correct else 0
            elif question.question_type == 'true_false':
                is_correct = answer == question.correct_answer
                score = test.true_false_score if is_correct else 0
            elif question.question_type == 'fill_blank':
                def norm_fill(s):
                    parts = [p.strip().lower() for p in s.replace('、', ',').split(',') if p.strip()]
                    return ','.join(parts)
                is_correct = norm_fill(answer) == norm_fill(question.correct_answer)
                score = test.fill_blank_score if is_correct else 0
            elif question.question_type == 'short_answer':
                # 简答题需要教师手动评分
                score = 0
            
            questions.append({
                'id': question.id,
                'content': question.content,
                'question_type': question.question_type,
                'option_a': question.option_a,
                'option_b': question.option_b,
                'option_c': question.option_c,
                'option_d': question.option_d,
                'student_answer': answer,
                'correct_answer': question.correct_answer,
                'is_correct': is_correct,
                'score': score,
                'explanation': question.explanation
            })
    
    return render_template('test_result.html',
                         test=test,
                         result=result,
                         student=student,
                         history=history,
                         questions=questions,
                         is_teacher=session.get('role') == 'teacher',
                         test_id=test.id if test else None)

@app.route('/student_dashboard')
def student_dashboard():
    if 'student_id' not in session:
        return redirect(url_for('student_start'))
    
    # 获取学生信息
    student = User.query.get(session['student_id'])
    
    # 获取当前测试
    current_test = Test.query.filter_by(is_active=True).first()
    
    # 获取学生历史记录
    history = StudentTestHistory.query.filter_by(
        student_id=session['student_id']
    ).first()
    
    if not history:
        history = StudentTestHistory(
            student_id=session['student_id'],
            student_name=session.get('student_name', ''),
            class_number=session.get('class_number', ''),
            test_count=0,
            total_score=0,
            average_score=0,
            highest_score=0,
            lowest_score=0
        )
        db.session.add(history)
        db.session.commit()
    
    # 获取学生的测试结果
    test_results = TestResult.query.filter_by(
        student_id=session['student_id']
    ).order_by(TestResult.created_at.desc()).all()
    
    return render_template('student_dashboard.html',
                         student=student,
                         current_test=current_test,
                         history=history,
                         test_results=test_results)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('student_start'))

@app.route('/export_questions/<question_type>')
def export_questions(question_type):
    if 'role' not in session or session['role'] != 'teacher':
        flash('未授权')
        return redirect(url_for('teacher_dashboard'))
    questions = Question.query.filter_by(question_type=question_type).all()
    if not questions:
        flash('题库为空')
        return redirect(url_for('teacher_dashboard'))
    data = []
    if question_type == 'single_choice':
        columns = ['题干', '选项A', '选项B', '选项C', '选项D', '正确答案', '分值', '解析']
        for q in questions:
            data.append([
                q.content, q.option_a, q.option_b, q.option_c, q.option_d, q.correct_answer, q.score, q.explanation
            ])
    elif question_type == 'multiple_choice':
        columns = ['题干', '选项A', '选项B', '选项C', '选项D', '选项E', '正确答案', '分值', '解析']
        for q in questions:
            data.append([
                q.content, q.option_a, q.option_b, q.option_c, q.option_d, q.option_e, q.correct_answer, q.score, q.explanation
            ])
    elif question_type == 'true_false':
        columns = ['题干', '正确答案', '分值', '解析']
        for q in questions:
            data.append([
                q.content, q.correct_answer, q.score, q.explanation
            ])
    else:
        columns = ['题干', '正确答案', '分值', '解析']
        for q in questions:
            data.append([
                q.content, q.correct_answer, q.score, q.explanation
            ])
    df = pd.DataFrame(data, columns=columns)
    output = BytesIO()
    df.to_excel(output, index=False)
    output.seek(0)
    filename = f"{question_type}_questions_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    return send_file(output, as_attachment=True, download_name=filename, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

# 题库管理API
@app.route('/api/question_banks')
def get_question_banks_api():
    if 'role' not in session or session['role'] != 'teacher':
        return jsonify({'error': 'Unauthorized'}), 401
    
    banks = QuestionBank.query.all()
    result = {
        'single_choice': [],
        'multiple_choice': [],
        'true_false': [],
        'fill_blank': [],
        'short_answer': []
    }
    
    for bank in banks:
        bank_data = {
            'id': bank.id,
            'name': bank.name,
            'question_count': Question.query.filter_by(bank_id=bank.id).count()
        }
        result[bank.question_type].append(bank_data)
    
    return jsonify(result)

@app.route('/api/question_bank', methods=['POST'])
def create_question_bank():
    if 'role' not in session or session['role'] != 'teacher':
        return jsonify({'error': '未登录'}), 401
    data = request.json
    name = data.get('name')
    question_type = data.get('question_type')
    if not name or not question_type:
        return jsonify({'error': '参数缺失'}), 400
    bank = QuestionBank(name=name, question_type=question_type)
    db.session.add(bank)
    db.session.commit()
    return jsonify({'success': True, 'id': bank.id})

@app.route('/api/question_bank/<int:bank_id>', methods=['PUT'])
def rename_question_bank(bank_id):
    if 'role' not in session or session['role'] != 'teacher':
        return jsonify({'error': '未登录'}), 401
    data = request.json
    name = data.get('name')
    bank = QuestionBank.query.get(bank_id)
    if not bank:
        return jsonify({'error': '题库不存在'}), 404
    bank.name = name
    db.session.commit()
    return jsonify({'success': True})

@app.route('/api/question_bank/<int:bank_id>', methods=['DELETE'])
def delete_question_bank(bank_id):
    if 'role' not in session or session['role'] != 'teacher':
        return jsonify({'error': '未登录'}), 401
    bank = QuestionBank.query.get(bank_id)
    if not bank:
        return jsonify({'error': '题库不存在'}), 404
    db.session.delete(bank)
    db.session.commit()
    return jsonify({'success': True})

@app.route('/api/question_bank/<int:bank_id>/questions', methods=['GET'])
def get_bank_questions(bank_id):
    if 'role' not in session or session['role'] != 'teacher':
        return jsonify({'error': '未登录'}), 401
    bank = QuestionBank.query.get(bank_id)
    if not bank:
        return jsonify({'error': '题库不存在'}), 404
    questions = []
    for q in bank.questions:
        questions.append({
            'id': q.id,
            'content': q.content,
            'option_a': q.option_a,
            'option_b': q.option_b,
            'option_c': q.option_c,
            'option_d': q.option_d,
            'option_e': q.option_e,
            'correct_answer': q.correct_answer,
            'score': q.score,
            'explanation': q.explanation
        })
    return jsonify({'questions': questions, 'bank_name': bank.name, 'question_type': bank.question_type})

@app.route('/api/question_bank/<int:bank_id>/questions', methods=['POST'])
def save_bank_questions(bank_id):
    if 'role' not in session or session['role'] != 'teacher':
        return jsonify({'error': '未登录'}), 401
    bank = QuestionBank.query.get(bank_id)
    if not bank:
        return jsonify({'error': '题库不存在'}), 404
    data = request.json
    questions = data.get('questions', [])
    # 先清空原有题目
    for q in bank.questions:
        db.session.delete(q)
    db.session.commit()
    # 新增题目
    for q in questions:
        question = Question(
            question_type=bank.question_type,
            content=q.get('content'),
            option_a=q.get('option_a'),
            option_b=q.get('option_b'),
            option_c=q.get('option_c'),
            option_d=q.get('option_d'),
            option_e=q.get('option_e'),
            correct_answer=q.get('correct_answer'),
            score=q.get('score'),
            explanation=q.get('explanation'),
            bank_id=bank.id
        )
        db.session.add(question)
    db.session.commit()
    return jsonify({'success': True})

@app.route('/teacher/bank/<int:bank_id>')
def teacher_bank(bank_id):
    if 'role' not in session or session['role'] != 'teacher':
        return redirect(url_for('teacher_login'))
    
    bank = QuestionBank.query.get_or_404(bank_id)
    questions = Question.query.filter_by(bank_id=bank_id).all()
    
    return render_template('bank_content.html', bank=bank, questions=questions)

@app.route('/api/bank/<int:bank_id>/rename', methods=['POST'])
def rename_bank(bank_id):
    if 'role' not in session or session['role'] != 'teacher':
        return jsonify({'error': 'Unauthorized'}), 401
    
    bank = QuestionBank.query.get_or_404(bank_id)
    data = request.get_json()
    bank.name = data.get('name')
    db.session.commit()
    return jsonify({'success': True})

@app.route('/api/bank/<int:bank_id>', methods=['DELETE'])
def delete_bank(bank_id):
    if 'role' not in session or session['role'] != 'teacher':
        return jsonify({'error': 'Unauthorized'}), 401
    
    bank = QuestionBank.query.get_or_404(bank_id)
    Question.query.filter_by(bank_id=bank_id).delete()
    db.session.delete(bank)
    db.session.commit()
    return jsonify({'success': True})

# ----- 预设API -----

@app.route('/save_test_settings', methods=['POST'])
def save_test_settings():
    if 'role' not in session or session['role'] != 'teacher':
        return redirect(url_for('teacher_login'))
    
    # 先将现有测试设为非激活状态，保证学生只能参加最新一次测试
    Test.query.update({Test.is_active: False})

    # 保存/更新预设
    preset_id = request.form.get('preset_id', type=int)
    if preset_id:
        preset = TestPreset.query.get(preset_id)
    else:
        preset = None

    if not preset:
        preset = TestPreset()
        db.session.add(preset)

    preset.title = request.form.get('test_title')
    preset.single_choice_count = request.form.get('single_choice_count', type=int)
    preset.single_choice_score = request.form.get('single_choice_score', type=int)
    preset.multiple_choice_count = request.form.get('multiple_choice_count', type=int)
    preset.multiple_choice_score = request.form.get('multiple_choice_score', type=int)
    preset.true_false_count = request.form.get('true_false_count', type=int)
    preset.true_false_score = request.form.get('true_false_score', type=int)
    preset.fill_blank_count = request.form.get('fill_blank_count', type=int)
    preset.fill_blank_score = request.form.get('fill_blank_score', type=int)
    preset.short_answer_count = request.form.get('short_answer_count', type=int)
    preset.short_answer_score = request.form.get('short_answer_score', type=int)
    preset.single_choice_bank_id = request.form.get('single_choice_bank', type=int)
    preset.multiple_choice_bank_id = request.form.get('multiple_choice_bank', type=int)
    preset.true_false_bank_id = request.form.get('true_false_bank', type=int)
    preset.fill_blank_bank_id = request.form.get('fill_blank_bank', type=int)
    preset.short_answer_bank_id = request.form.get('short_answer_bank', type=int)
    preset.allow_student_choice = bool(request.form.get('allow_student_choice'))

    # 创建新的 Test 记录
    test = Test()
    test.title = request.form.get('test_title')
    test.allow_student_choice = bool(request.form.get('allow_student_choice'))

    # 工具函数：根据bank_id获取题目数量
    def bank_size(bid):
        return Question.query.filter_by(bank_id=bid).count() if bid else 0

    # --- 单选题 ---
    sc_bank_id = request.form.get('single_choice_bank', type=int)
    sc_count_req = request.form.get('single_choice_count', type=int)
    sc_max = bank_size(sc_bank_id)
    test.single_choice_bank_id = sc_bank_id
    test.single_choice_count = min(sc_count_req or 0, sc_max)
    test.single_choice_score = request.form.get('single_choice_score', type=int)

    # --- 多选题 ---
    mc_bank_id = request.form.get('multiple_choice_bank', type=int)
    mc_count_req = request.form.get('multiple_choice_count', type=int)
    mc_max = bank_size(mc_bank_id)
    test.multiple_choice_bank_id = mc_bank_id
    test.multiple_choice_count = min(mc_count_req or 0, mc_max)
    test.multiple_choice_score = request.form.get('multiple_choice_score', type=int)

    # --- 判断题 ---
    tf_bank_id = request.form.get('true_false_bank', type=int)
    tf_count_req = request.form.get('true_false_count', type=int)
    tf_max = bank_size(tf_bank_id)
    test.true_false_bank_id = tf_bank_id
    test.true_false_count = min(tf_count_req or 0, tf_max)
    test.true_false_score = request.form.get('true_false_score', type=int)

    # --- 填空题 ---
    fb_bank_id = request.form.get('fill_blank_bank', type=int)
    fb_count_req = request.form.get('fill_blank_count', type=int)
    fb_max = bank_size(fb_bank_id)
    test.fill_blank_bank_id = fb_bank_id
    test.fill_blank_count = min(fb_count_req or 0, fb_max)
    test.fill_blank_score = request.form.get('fill_blank_score', type=int)

    # --- 简答题 ---
    sa_bank_id = request.form.get('short_answer_bank', type=int)
    sa_count_req = request.form.get('short_answer_count', type=int)
    sa_max = bank_size(sa_bank_id)
    test.short_answer_bank_id = sa_bank_id
    test.short_answer_count = min(sa_count_req or 0, sa_max)
    test.short_answer_score = request.form.get('short_answer_score', type=int)

    # 重新计算总分
    test.total_score = (
        (test.single_choice_count * (test.single_choice_score or 0)) +
        (test.multiple_choice_count * (test.multiple_choice_score or 0)) +
        (test.true_false_count * (test.true_false_score or 0)) +
        (test.fill_blank_count * (test.fill_blank_score or 0)) +
        (test.short_answer_count * (test.short_answer_score or 0))
    )

    # 创建新的 TestPreset 参数已上移
    # --- end counts / banks ---
    
    db.session.add(test)
    db.session.commit()
    
    flash('测试设置已保存')
    return redirect(url_for('teacher_dashboard'))

@app.route('/export_bank/<int:bank_id>')
def export_bank(bank_id):
    """导出指定题库为 Excel 文件"""
    if 'role' not in session or session['role'] != 'teacher':
        flash('未授权')
        return redirect(url_for('teacher_dashboard'))

    bank = QuestionBank.query.get_or_404(bank_id)
    questions = bank.questions
    if not questions:
        flash('题库为空')
        return redirect(url_for('teacher_bank', bank_id=bank_id))

    data = []
    qtype = bank.question_type
    if qtype == 'single_choice':
        columns = ['题干', '选项A', '选项B', '选项C', '选项D', '正确答案', '分值', '解析']
        for q in questions:
            data.append([q.content, q.option_a, q.option_b, q.option_c, q.option_d, q.correct_answer, q.score, q.explanation])
    elif qtype == 'multiple_choice':
        columns = ['题干', '选项A', '选项B', '选项C', '选项D', '选项E', '正确答案', '分值', '解析']
        for q in questions:
            data.append([q.content, q.option_a, q.option_b, q.option_c, q.option_d, q.option_e, q.correct_answer, q.score, q.explanation])
    elif qtype == 'true_false':
        columns = ['题干', '正确答案', '分值', '解析']
        for q in questions:
            data.append([q.content, q.correct_answer, q.score, q.explanation])
    else:  # fill_blank 或 short_answer
        columns = ['题干', '正确答案', '分值', '解析']
        for q in questions:
            data.append([q.content, q.correct_answer, q.score, q.explanation])

    df = pd.DataFrame(data, columns=columns)
    output = BytesIO()
    df.to_excel(output, index=False)
    output.seek(0)
    filename = f"{bank.name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    return send_file(output, as_attachment=True, download_name=filename, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

# 初始化数据库
def init_db():
    with app.app_context():
        db.create_all()

        # ---- 若旧表缺少新列，动态添加 ----
        def ensure_column(table, column, col_type):
            info = db.session.execute(text(f"PRAGMA table_info({table})")).fetchall()
            if column not in [row[1] for row in info]:
                db.session.execute(text(f"ALTER TABLE {table} ADD COLUMN {column} {col_type}"))
                db.session.commit()

        for col in [
            ('single_choice_bank_id', 'INTEGER'),
            ('multiple_choice_bank_id', 'INTEGER'),
            ('true_false_bank_id', 'INTEGER'),
            ('fill_blank_bank_id', 'INTEGER'),
            ('short_answer_bank_id', 'INTEGER'),
            ('allow_student_choice', 'BOOLEAN')]:
            ensure_column('test', col[0], col[1])

        for tbl,col in [
            ('test', 'single_choice_bank_id'),
            ('test', 'multiple_choice_bank_id'),
            ('test', 'true_false_bank_id'),
            ('test', 'fill_blank_bank_id'),
            ('test', 'short_answer_bank_id'),
            ('question', 'image_path'),
            ('short_answer_submission', 'image_path')
        ]:
            ensure_column(tbl, col, 'TEXT' if col.endswith('image_path') else 'INTEGER')
        
        # 为 test_preset 表添加 allow_student_choice 字段
        ensure_column('test_preset', 'allow_student_choice', 'BOOLEAN')

        # 默认管理员
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            admin = User(username='admin', role='teacher')
            admin.set_password('admin')
            db.session.add(admin)
            db.session.commit()

# 初始化数据库（无论作为脚本运行还是被WSGI加载）
init_db()

# ---- TestPreset API ----
@app.route('/api/test_presets')
def test_presets_list():
    if 'role' not in session or session['role'] != 'teacher':
        return jsonify([])
    presets = TestPreset.query.order_by(TestPreset.created_at.desc()).all()
    return jsonify([{'id': p.id, 'title': p.title} for p in presets])

@app.route('/api/test_presets/<int:preset_id>', methods=['GET', 'DELETE'])
def test_preset_detail(preset_id):
    if 'role' not in session or session['role'] != 'teacher':
        return jsonify({'error': 'unauthorized'}), 401
    if request.method == 'DELETE':
        p = TestPreset.query.get_or_404(preset_id)
        db.session.delete(p)
        db.session.commit()
        return jsonify({'success': True})

    p = TestPreset.query.get_or_404(preset_id)
    return jsonify({
        'id': p.id,
        'title': p.title,
        'single_choice_count': p.single_choice_count,
        'single_choice_score': p.single_choice_score,
        'multiple_choice_count': p.multiple_choice_count,
        'multiple_choice_score': p.multiple_choice_score,
        'true_false_count': p.true_false_count,
        'true_false_score': p.true_false_score,
        'fill_blank_count': p.fill_blank_count,
        'fill_blank_score': p.fill_blank_score,
        'short_answer_count': p.short_answer_count,
        'short_answer_score': p.short_answer_score,
        'single_choice_bank_id': p.single_choice_bank_id,
        'multiple_choice_bank_id': p.multiple_choice_bank_id,
        'true_false_bank_id': p.true_false_bank_id,
        'fill_blank_bank_id': p.fill_blank_bank_id,
        'short_answer_bank_id': p.short_answer_bank_id,
        'allow_student_choice': p.allow_student_choice
    })

# 新增：获取当前测试设置（公开API，学生可访问）
@app.route('/api/current_test_settings')
def current_test_settings():
    # 获取最新的测试设置
    last_test = Test.query.order_by(Test.created_at.desc()).first()
    if not last_test:
        return jsonify({'allow_student_choice': False})
    
    return jsonify({
        'allow_student_choice': last_test.allow_student_choice if hasattr(last_test, 'allow_student_choice') else False
    })

# 新增：公开获取测试预设列表（学生可访问）
@app.route('/api/test_presets_public')
def test_presets_public():
    presets = TestPreset.query.order_by(TestPreset.created_at.desc()).all()
    return jsonify([{'id': p.id, 'title': p.title} for p in presets])

# ----- 简答题批改 -----

@app.route('/grade_short_answer/<int:sa_id>', methods=['GET', 'POST'])
def grade_short_answer(sa_id):
    if 'role' not in session or session['role'] != 'teacher':
        return redirect(url_for('teacher_login'))
    sa = ShortAnswerSubmission.query.get_or_404(sa_id)
    question = Question.query.get(sa.question_id)
    if request.method == 'POST':
        sa.score = request.form.get('score', type=int)
        sa.comment = request.form.get('comment')
        sa.graded_bool = True
        # 更新 TestResult 总分
        tr = TestResult.query.get(sa.result_id)
        # 先扣除旧分再加新分
        old = sa.score or 0
        delta = sa.score - old
        tr.score = (tr.score or 0) + delta
        db.session.commit()
        flash('批改已保存')
        return redirect(url_for('short_answer_list'))
    return render_template('grade_short_answer.html', sa=sa, question=question)

# 未批改列表
@app.route('/short_answers')
def short_answer_list():
    if 'role' not in session or session['role'] != 'teacher':
        return redirect(url_for('teacher_login'))
    pending = ShortAnswerSubmission.query.filter_by(graded_bool=False).order_by(ShortAnswerSubmission.created_at).all()
    return render_template('short_answer_list.html', submissions=pending)

@app.route('/api/upload_image', methods=['POST'])
def upload_image():
    if 'file' not in request.files:
        return jsonify({'error':'no file'}),400
    f=request.files['file']
    if f.filename=='':
        return jsonify({'error':'empty'}),400
    ext=f.filename.rsplit('.',1)[-1].lower()
    if ext not in ALLOWED_IMG_EXT:
        return jsonify({'error':'ext'}),400
    f.seek(0,2); size=f.tell(); f.seek(0)
    if size>MAX_IMG_SIZE:
        return jsonify({'error':'size'}),400
    day=datetime.now().strftime('%Y%m%d')
    save_dir=os.path.join('static','uploads',day)
    os.makedirs(save_dir, exist_ok=True)
    filename=secure_filename(str(uuid.uuid4())+'.'+ext)
    path=os.path.join(save_dir,filename)
    f.save(path)
    return jsonify({'url':'/'+path.replace('\\','/')})

if __name__ == '__main__':
    init_db()
    app.run(debug=True, host='0.0.0.0', port=8000) 