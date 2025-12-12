"""
AI批改功能安装验证脚本
检查所有必要的组件和配置是否正确
"""

import os
import sys
import importlib.util
from pathlib import Path

def check_file_exists(filepath, description):
    """检查文件是否存在"""
    if os.path.exists(filepath):
        print(f"✅ {description}: {filepath}")
        return True
    else:
        print(f"❌ {description}缺失: {filepath}")
        return False

def check_config():
    """检查配置文件"""
    print("\n📋 检查配置文件...")
    
    try:
        from config import AI_GRADING_CONFIG, AI_GRADING_PROMPTS
        
        # 检查必要的配置项
        required_keys = ['provider', 'api_key', 'model', 'enabled']
        missing_keys = []
        
        for key in required_keys:
            if key not in AI_GRADING_CONFIG:
                missing_keys.append(key)
        
        if missing_keys:
            print(f"❌ 配置缺失项: {missing_keys}")
            return False
        
        # 检查API密钥
        if not AI_GRADING_CONFIG.get('api_key'):
            print("⚠️  API密钥未配置")
            return False
        
        # 检查是否启用
        if not AI_GRADING_CONFIG.get('enabled'):
            print("⚠️  AI批改功能未启用 (enabled=False)")
            return False
        
        print("✅ 配置文件检查通过")
        print(f"   提供商: {AI_GRADING_CONFIG.get('provider')}")
        print(f"   模型: {AI_GRADING_CONFIG.get('model')}")
        print(f"   状态: {'启用' if AI_GRADING_CONFIG.get('enabled') else '禁用'}")
        return True
        
    except ImportError as e:
        print(f"❌ 无法导入配置: {e}")
        return False
    except Exception as e:
        print(f"❌ 配置检查失败: {e}")
        return False

def check_dependencies():
    """检查依赖包"""
    print("\n📦 检查依赖包...")
    
    required_packages = [
        ('requests', '用于API请求'),
        ('flask', 'Web框架'),
        ('sqlalchemy', '数据库ORM'),
        ('pandas', '数据处理')
    ]
    
    missing_packages = []
    
    for package, description in required_packages:
        try:
            __import__(package)
            print(f"✅ {package}: {description}")
        except ImportError:
            print(f"❌ {package}: {description} - 未安装")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\n⚠️  缺失依赖包: {missing_packages}")
        print("请运行: pip install " + " ".join(missing_packages))
        return False
    
    return True

def check_ai_service():
    """检查AI服务"""
    print("\n🤖 检查AI批改服务...")
    
    try:
        from ai_grading_service import get_ai_grading_service
        
        ai_service = get_ai_grading_service()
        
        if ai_service.is_enabled():
            print("✅ AI批改服务可用")
            
            # 进行简单测试
            success, result = ai_service.grade_answer(
                question="测试题目",
                reference_answer="测试参考答案",
                student_answer="测试学生答案",
                max_score=10
            )
            
            if success:
                print("✅ AI批改测试成功")
                print(f"   测试得分: {result.get('score')}分")
                return True
            else:
                print(f"❌ AI批改测试失败: {result.get('error_message')}")
                return False
        else:
            print("❌ AI批改服务不可用")
            return False
            
    except Exception as e:
        print(f"❌ AI服务检查失败: {e}")
        return False

def check_database():
    """检查数据库结构"""
    print("\n🗄️  检查数据库结构...")
    
    try:
        from app import app, db, Test, TestPreset, ShortAnswerSubmission
        
        with app.app_context():
            # 检查表是否存在
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            tables = inspector.get_table_names()
            required_tables = ['test', 'test_preset', 'short_answer_submission']
            
            missing_tables = []
            for table in required_tables:
                if table not in tables:
                    missing_tables.append(table)
            
            if missing_tables:
                print(f"❌ 缺失数据表: {missing_tables}")
                return False
            
            # 检查新字段是否存在
            try:
                # 尝试查询新字段
                test = Test.query.first()
                if test:
                    _ = test.short_answer_grading_method
                
                preset = TestPreset.query.first()
                if preset:
                    _ = preset.short_answer_grading_method
                
                submission = ShortAnswerSubmission.query.first()
                if submission:
                    _ = submission.grading_method
                    _ = submission.ai_original_score
                    _ = submission.ai_feedback
                    _ = submission.manual_reviewed
                
                print("✅ 数据库结构检查通过")
                return True
                
            except AttributeError as e:
                print(f"❌ 数据库字段缺失: {e}")
                print("请运行: python migrate_ai_grading.py")
                return False
                
    except Exception as e:
        print(f"❌ 数据库检查失败: {e}")
        return False

def main():
    """主验证函数"""
    print("🔍 AI批改功能安装验证")
    print("=" * 50)
    
    # 检查核心文件
    print("\n📁 检查核心文件...")
    files_ok = True
    files_ok &= check_file_exists("config.py", "配置文件")
    files_ok &= check_file_exists("ai_grading_service.py", "AI批改服务")
    files_ok &= check_file_exists("app.py", "主应用文件")
    files_ok &= check_file_exists("migrate_ai_grading.py", "数据库迁移脚本")
    files_ok &= check_file_exists("templates/teacher_dashboard.html", "教师面板模板")
    files_ok &= check_file_exists("templates/test_result.html", "测试结果模板")
    
    # 检查各个组件
    config_ok = check_config()
    deps_ok = check_dependencies()
    ai_ok = check_ai_service()
    db_ok = check_database()
    
    # 总结
    print("\n" + "=" * 50)
    print("📊 验证结果总结:")
    print(f"   文件检查: {'✅ 通过' if files_ok else '❌ 失败'}")
    print(f"   配置检查: {'✅ 通过' if config_ok else '❌ 失败'}")
    print(f"   依赖检查: {'✅ 通过' if deps_ok else '❌ 失败'}")
    print(f"   AI服务: {'✅ 通过' if ai_ok else '❌ 失败'}")
    print(f"   数据库: {'✅ 通过' if db_ok else '❌ 失败'}")
    
    all_ok = files_ok and config_ok and deps_ok and ai_ok and db_ok
    
    if all_ok:
        print("\n🎉 所有检查通过！AI批改功能已准备就绪！")
        print("\n📋 下一步操作:")
        print("   1. 启动应用: python app.py")
        print("   2. 访问教师面板: http://127.0.0.1:8000/teacher/login")
        print("   3. 导入简答题题库")
        print("   4. 创建启用AI批改的测试")
        print("   5. 测试学生答题和AI批改功能")
    else:
        print("\n⚠️  部分检查未通过，请根据上述提示修复问题")
        
    return all_ok

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)