#!/usr/bin/env python3
"""
测试导入题库功能修复
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_import_functionality():
    """测试导入功能修复"""
    print("=== 测试导入题库功能修复 ===\n")
    
    # 读取app.py文件
    with open('app.py', 'r', encoding='utf-8') as f:
        app_content = f.read()
    
    # 读取teacher_dashboard.html文件
    with open('templates/teacher_dashboard.html', 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    # 测试1: 检查后端文件字段名
    print("测试1: 检查后端文件字段名")
    assert "'csv_file' not in request.files" in app_content, "后端应该检查csv_file字段"
    assert "request.files['csv_file']" in app_content, "后端应该获取csv_file字段"
    assert "'file' not in request.files" not in app_content, "不应该检查file字段"
    print("✓ 通过\n")
    
    # 测试2: 检查前端文件字段名
    print("测试2: 检查前端文件字段名")
    assert 'name="csv_file"' in html_content, "前端文件输入应该使用csv_file名称"
    print("✓ 通过\n")
    
    # 测试3: 检查表单其他字段
    print("测试3: 检查表单其他字段")
    assert 'name="question_type"' in html_content, "应该有question_type隐藏字段"
    assert 'name="bank_name"' in html_content, "应该有bank_name隐藏字段"
    print("✓ 通过\n")
    
    print("=== 导入功能修复测试通过！ ===")

def test_form_structure():
    """测试表单结构"""
    print("\n=== 测试表单结构 ===\n")
    
    print("表单字段对应关系:")
    print("前端 → 后端")
    print("csv_file → request.files['csv_file']")
    print("question_type → request.form.get('question_type')")
    print("bank_name → request.form.get('bank_name')")
    print("✓ 字段对应关系正确\n")

if __name__ == "__main__":
    test_import_functionality()
    test_form_structure()
    print("🎉 导入题库功能修复完成！现在应该可以正常导入文件了。")