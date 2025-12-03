from app import app, db, User

with app.app_context():
    # 检查是否已有教师账号
    teacher = User.query.filter_by(role='teacher').first()
    if teacher:
        print(f"已有教师账号：{teacher.username}")
    else:
        # 创建默认教师账号
        teacher = User(username='admin', role='teacher')
        teacher.set_password('admin')
        db.session.add(teacher)
        db.session.commit()
        print("已创建默认教师账号：")
        print(f"用户名：admin")
        print(f"密码：admin")