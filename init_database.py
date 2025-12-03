"""
数据库初始化脚本
用于创建数据库表和默认教师账户
"""

from app import app, db, User, init_db

def main():
    """初始化数据库"""
    print("开始初始化数据库...")
    
    # 调用初始化函数
    result = init_db()
    
    if result:
        print("\n数据库初始化成功！")
        
        # 验证教师账户
        with app.app_context():
            admin = User.query.filter_by(username='admin', role='teacher').first()
            if admin:
                print(f"\n✓ 默认教师账户已创建")
                print(f"  用户名: admin")
                print(f"  密码: admin")
                print(f"  角色: {admin.role}")
                print(f"\n⚠ 请在首次登录后立即修改密码！")
            else:
                print("\n✗ 警告：默认教师账户未找到")
    else:
        print("\n✗ 数据库初始化失败")
        return 1
    
    return 0

if __name__ == '__main__':
    exit(main())
