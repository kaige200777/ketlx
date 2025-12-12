"""
测试AI批改功能
"""

from ai_grading_service import get_ai_grading_service

def test_ai_grading():
    """测试AI批改服务"""
    print("测试AI批改功能...")
    
    # 获取AI批改服务
    ai_service = get_ai_grading_service()
    
    # 检查服务是否可用
    print(f"AI批改服务状态: {'可用' if ai_service.is_enabled() else '不可用'}")
    
    if not ai_service.is_enabled():
        print("AI批改服务不可用，请检查config.py中的配置")
        return
    
    # 测试批改一个简答题
    question = "请简述计算机网络的基本概念和作用。"
    reference_answer = "计算机网络是指将地理位置不同的具有独立功能的多台计算机及其外部设备，通过通信线路连接起来，在网络操作系统、网络管理软件及网络通信协议的管理和协调下，实现资源共享和信息传递的计算机系统。主要作用包括：资源共享、信息传递、分布式处理、提高可靠性等。"
    student_answer = "计算机网络就是把很多电脑连接在一起，可以共享文件和上网。"
    max_score = 10
    
    print(f"\n题目: {question}")
    print(f"参考答案: {reference_answer}")
    print(f"学生答案: {student_answer}")
    print(f"满分: {max_score}分")
    
    # 调用AI批改
    success, result = ai_service.grade_answer(
        question=question,
        reference_answer=reference_answer,
        student_answer=student_answer,
        max_score=max_score
    )
    
    if success:
        print(f"\n✓ AI批改成功!")
        print(f"得分: {result['score']}分")
        print(f"反馈: {result['feedback']}")
    else:
        print(f"\n✗ AI批改失败: {result.get('error_message', '未知错误')}")

if __name__ == '__main__':
    test_ai_grading()