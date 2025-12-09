"""
清理项目，准备进入生产环境
将文档移到docs目录，删除临时测试文件
"""
import os
import shutil

# 创建docs目录
if not os.path.exists('docs'):
    os.makedirs('docs')
    print("✓ 创建 docs 目录")

# 需要移动到docs目录的文档文件
docs_to_move = [
    'ALL_FIXES_SUMMARY.md',
    'BANK_EDIT_FIX.md',
    'BANK_LIST_DISPLAY_FIX.md',
    'BANK_MANAGEMENT_FIX.md',
    'CONTINUATION_SUMMARY.md',
    'DEBUGGING_SUMMARY.md',
    'DISABLE_BUTTON_NO_TEST_FIX.md',
    'FILE_UPLOAD_FIX.md',
    'FINAL_TEST_GUIDE.md',
    'IMAGE_UPLOAD_FIX.md',
    'IMPORT_FIX_SUMMARY.md',
    'IMPORT_UI_FIX.md',
    'LOGIN_FIX_SUMMARY.md',
    'NO_TEST_AVAILABLE_FIX.md',
    'PRESET_DISPLAY_FIX.md',
    'QUICK_TEST_GUIDE.md',
    'SCORING_ISSUE_EXPLANATION.md',
    'SHORT_ANSWER_DISPLAY_FIX.md',
    'TEMPLATE_COLUMNS_SPEC.md',
    'TEMPLATE_IMPORT_FIX.md',
    'ZERO_SCORE_WARNING_FIX.md',
    # 新增的修复文档
    'FILL_BLANK_DIAGNOSIS.md',
    'FILL_BLANK_SUBMIT_FIX.md',
    'SHORT_ANSWER_LIMIT_FIX.md',
]

# 需要删除的临时测试文件
files_to_delete = [
    'check_columns.py',
    'check_test_settings.py',
    'debug_display_logic.py',
    'debug_scoring.py',
    'debug_test_config.py',
    'test_api.py',
    'test_file_upload.py',
    'test_full_import.py',
    'test_import_fix.py',
    'test_import.py',
    'test_login.py',
    'test_preset_display.py',
    'test_presets_api.py',
    'test_statistics.html',
    'test_template_import.py',
    # 新增的调试文件
    'check_fill_blank_questions.py',
    'check_test_23_results.py',
    'debug_fill_blank_in_result.py',
    'test_fill_blank_stats.py',
]

print("\n" + "=" * 60)
print("开始清理项目文件")
print("=" * 60)

# 移动文档文件
print("\n1. 移动文档文件到 docs 目录:")
print("-" * 60)
moved_count = 0
for doc in docs_to_move:
    if os.path.exists(doc):
        try:
            shutil.move(doc, os.path.join('docs', doc))
            print(f"  ✓ 移动: {doc}")
            moved_count += 1
        except Exception as e:
            print(f"  ✗ 移动失败 {doc}: {e}")
    else:
        print(f"  - 文件不存在: {doc}")

print(f"\n已移动 {moved_count} 个文档文件")

# 删除临时测试文件
print("\n2. 删除临时测试文件:")
print("-" * 60)
deleted_count = 0
for file in files_to_delete:
    if os.path.exists(file):
        try:
            os.remove(file)
            print(f"  ✓ 删除: {file}")
            deleted_count += 1
        except Exception as e:
            print(f"  ✗ 删除失败 {file}: {e}")
    else:
        print(f"  - 文件不存在: {file}")

print(f"\n已删除 {deleted_count} 个临时文件")

# 保留的重要文件
print("\n3. 保留的重要文件:")
print("-" * 60)
important_files = [
    'app.py',
    'models.py',
    'run.py',
    'init_database.py',
    'create_teacher.py',
    'version.py',
    'wsgl.py',
    'requirements.txt',
    'README.md',
    'CHANGELOG.md',
    '.gitignore',
]

for file in important_files:
    if os.path.exists(file):
        print(f"  ✓ {file}")
    else:
        print(f"  ✗ 缺失: {file}")

print("\n" + "=" * 60)
print("清理完成！")
print("=" * 60)
print("\n提示：")
print("  - 所有修复文档已移动到 docs/ 目录")
print("  - 临时测试文件已删除")
print("  - 核心应用文件保持不变")
print("  - 可以安全地部署到生产环境")
print("\n下一步：")
print("  1. 检查 requirements.txt 确保所有依赖都已列出")
print("  2. 运行 python init_database.py 初始化数据库")
print("  3. 运行 python create_teacher.py 创建管理员账户")
print("  4. 启动应用: python run.py")
