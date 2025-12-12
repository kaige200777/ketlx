"""
数据库迁移脚本 - 添加AI批改功能相关字段
"""

from app import app, db
from sqlalchemy import text

def migrate_database():
    """执行数据库迁移"""
    with app.app_context():
        try:
            print("开始数据库迁移...")
            
            # 检查并添加Test表的新字段
            try:
                db.session.execute(text("ALTER TABLE test ADD COLUMN short_answer_grading_method VARCHAR(20) DEFAULT 'manual'"))
                print("✓ 已为Test表添加short_answer_grading_method字段")
            except Exception as e:
                if "duplicate column name" in str(e).lower() or "already exists" in str(e).lower():
                    print("✓ Test表的short_answer_grading_method字段已存在")
                else:
                    print(f"⚠ 添加Test表字段时出错: {e}")
            
            # 检查并添加TestPreset表的新字段
            try:
                db.session.execute(text("ALTER TABLE test_preset ADD COLUMN short_answer_grading_method VARCHAR(20) DEFAULT 'manual'"))
                print("✓ 已为TestPreset表添加short_answer_grading_method字段")
            except Exception as e:
                if "duplicate column name" in str(e).lower() or "already exists" in str(e).lower():
                    print("✓ TestPreset表的short_answer_grading_method字段已存在")
                else:
                    print(f"⚠ 添加TestPreset表字段时出错: {e}")
            
            # 检查并添加ShortAnswerSubmission表的新字段
            try:
                db.session.execute(text("ALTER TABLE short_answer_submission ADD COLUMN grading_method VARCHAR(20) DEFAULT 'manual'"))
                print("✓ 已为ShortAnswerSubmission表添加grading_method字段")
            except Exception as e:
                if "duplicate column name" in str(e).lower() or "already exists" in str(e).lower():
                    print("✓ ShortAnswerSubmission表的grading_method字段已存在")
                else:
                    print(f"⚠ 添加ShortAnswerSubmission表grading_method字段时出错: {e}")
            
            try:
                db.session.execute(text("ALTER TABLE short_answer_submission ADD COLUMN ai_original_score INTEGER"))
                print("✓ 已为ShortAnswerSubmission表添加ai_original_score字段")
            except Exception as e:
                if "duplicate column name" in str(e).lower() or "already exists" in str(e).lower():
                    print("✓ ShortAnswerSubmission表的ai_original_score字段已存在")
                else:
                    print(f"⚠ 添加ShortAnswerSubmission表ai_original_score字段时出错: {e}")
            
            try:
                db.session.execute(text("ALTER TABLE short_answer_submission ADD COLUMN ai_feedback TEXT"))
                print("✓ 已为ShortAnswerSubmission表添加ai_feedback字段")
            except Exception as e:
                if "duplicate column name" in str(e).lower() or "already exists" in str(e).lower():
                    print("✓ ShortAnswerSubmission表的ai_feedback字段已存在")
                else:
                    print(f"⚠ 添加ShortAnswerSubmission表ai_feedback字段时出错: {e}")
            
            try:
                db.session.execute(text("ALTER TABLE short_answer_submission ADD COLUMN manual_reviewed BOOLEAN DEFAULT 0"))
                print("✓ 已为ShortAnswerSubmission表添加manual_reviewed字段")
            except Exception as e:
                if "duplicate column name" in str(e).lower() or "already exists" in str(e).lower():
                    print("✓ ShortAnswerSubmission表的manual_reviewed字段已存在")
                else:
                    print(f"⚠ 添加ShortAnswerSubmission表manual_reviewed字段时出错: {e}")
            
            # 提交更改
            db.session.commit()
            print("✓ 数据库迁移完成")
            
        except Exception as e:
            db.session.rollback()
            print(f"✗ 数据库迁移失败: {e}")
            raise

if __name__ == '__main__':
    migrate_database()