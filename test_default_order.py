#!/usr/bin/env python3
"""
测试填空题默认按顺序的新规则
"""

from ai_grading_service import get_ai_grading_service

def test_default_order_rule():
    """测试默认按顺序的规则"""
    ai_service = get_ai_grading_service()
    
    if not ai_service.is_enabled():
        print("❌ AI批改服务未启用")
        return
    
    # 测试用例1：普通填空题（默认需要按顺序）
    print("=== 测试用例1：普通填空题（默认按顺序） ===")
    success, result = ai_service.grade_answer(
        question="计算下列各题：4*3*3+15/6*3=___，8%5/2+2=___",
        reference_answer="114、3",
        student_answer="3、114",  # 顺序错误
        max_score=8,
        question_type='fill_blank'
    )
    
    if success:
        print(f"得分: {result['score']}/8")
        print(f"需要顺序: {result.get('order_required', '未知')}")
        print(f"简短理由: {result.get('short_reason', '无')}")
        print(f"完整反馈: {result['feedback'][:150]}...")
    else:
        print(f"❌ 测试失败: {result}")
    
    print("\n" + "="*60 + "\n")
    
    # 测试用例2：明确说明不需要顺序的填空题
    print("=== 测试用例2：明确说明不需要顺序 ===")
    success, result = ai_service.grade_answer(
        question="列举计算机的组成部分（顺序不限）：___、___、___",
        reference_answer="CPU、内存、硬盘",
        student_answer="硬盘、CPU、内存",  # 顺序不同但内容正确
        max_score=6,
        question_type='fill_blank'
    )
    
    if success:
        print(f"得分: {result['score']}/6")
        print(f"需要顺序: {result.get('order_required', '未知')}")
        print(f"简短理由: {result.get('short_reason', '无')}")
        print(f"完整反馈: {result['feedback'][:150]}...")
    else:
        print(f"❌ 测试失败: {result}")
    
    print("\n" + "="*60 + "\n")
    
    # 测试用例3：数学计算题（默认按顺序）
    print("=== 测试用例3：数学计算题（默认按顺序） ===")
    success, result = ai_service.grade_answer(
        question="解方程：x+2=5，x=___；2x=10，x=___",
        reference_answer="3、5",
        student_answer="3、5",  # 正确顺序
        max_score=4,
        question_type='fill_blank'
    )
    
    if success:
        print(f"得分: {result['score']}/4")
        print(f"需要顺序: {result.get('order_required', '未知')}")
        print(f"简短理由: {result.get('short_reason', '无')}")
        print(f"完整反馈: {result['feedback'][:150]}...")
    else:
        print(f"❌ 测试失败: {result}")

if __name__ == '__main__':
    test_default_order_rule()