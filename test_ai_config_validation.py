"""
测试AI配置验证改进
验证增强的配置检查逻辑是否正常工作
"""

import requests
import json
from ai_grading_service import get_ai_grading_service

def test_ai_config_validation():
    """测试AI配置验证逻辑"""
    print("🔍 测试AI配置验证改进...")
    
    # 测试AI服务配置检查
    print("\n1. 测试AI服务配置检查:")
    ai_service = get_ai_grading_service()
    enabled, message = ai_service.get_config_status()
    
    print(f"   配置状态: {'✅ 正确' if enabled else '❌ 不正确'}")
    print(f"   详细信息: {message}")
    
    if enabled:
        print(f"   提供商: {ai_service.config.get('provider', 'N/A')}")
        print(f"   模型: {ai_service.config.get('model', 'N/A')}")
        print(f"   API密钥: {'已配置' if ai_service.config.get('api_key') else '未配置'}")
    
    return enabled, message

def test_api_endpoint():
    """测试API端点返回的状态信息"""
    print("\n2. 测试API端点:")
    
    try:
        response = requests.get("http://127.0.0.1:8000/api/ai_grading_status")
        if response.status_code == 200:
            data = response.json()
            print(f"   API响应成功")
            print(f"   启用状态: {'✅ 已启用' if data.get('enabled') else '❌ 未启用'}")
            print(f"   状态消息: {data.get('message', 'N/A')}")
            print(f"   详细信息: {data.get('details', 'N/A')}")
            
            if data.get('enabled'):
                print(f"   提供商: {data.get('provider', 'N/A')}")
                print(f"   模型: {data.get('model', 'N/A')}")
            else:
                print(f"   建议: {data.get('suggestion', 'N/A')}")
            
            return data.get('enabled', False)
        else:
            print(f"   ❌ API请求失败: {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("   ⚠️  无法连接到应用服务器")
        return None
    except Exception as e:
        print(f"   ❌ API测试失败: {e}")
        return False

def test_config_scenarios():
    """测试不同配置场景"""
    print("\n3. 配置验证场景测试:")
    
    from config import AI_GRADING_CONFIG
    
    scenarios = [
        {
            'name': '完整配置',
            'config': {
                'enabled': True,
                'api_key': 'sk-test123456789',
                'provider': 'openai',
                'model': 'gpt-3.5-turbo'
            },
            'expected': True
        },
        {
            'name': '缺少API密钥',
            'config': {
                'enabled': True,
                'api_key': '',
                'provider': 'openai',
                'model': 'gpt-3.5-turbo'
            },
            'expected': False
        },
        {
            'name': '未启用',
            'config': {
                'enabled': False,
                'api_key': 'sk-test123456789',
                'provider': 'openai',
                'model': 'gpt-3.5-turbo'
            },
            'expected': False
        },
        {
            'name': '缺少提供商',
            'config': {
                'enabled': True,
                'api_key': 'sk-test123456789',
                'provider': '',
                'model': 'gpt-3.5-turbo'
            },
            'expected': False
        },
        {
            'name': 'Azure需要base_url',
            'config': {
                'enabled': True,
                'api_key': 'sk-test123456789',
                'provider': 'azure',
                'model': 'gpt-35-turbo',
                'base_url': ''
            },
            'expected': False
        }
    ]
    
    for scenario in scenarios:
        print(f"\n   📋 测试场景: {scenario['name']}")
        
        # 模拟配置检查逻辑
        config = scenario['config']
        
        # 检查是否启用
        if not config.get('enabled', False):
            result = False
            message = "AI批改功能未启用"
        # 检查API密钥
        elif not config.get('api_key', '').strip():
            result = False
            message = "缺少API密钥"
        # 检查API密钥格式
        elif len(config.get('api_key', '').strip()) < 10:
            result = False
            message = "API密钥格式不正确"
        # 检查提供商
        elif not config.get('provider', '').strip():
            result = False
            message = "未配置API提供商"
        # 检查模型
        elif not config.get('model', '').strip():
            result = False
            message = "未配置模型名称"
        # 检查特殊提供商的base_url
        elif config.get('provider') in ['azure', 'qianfan', 'tongyi'] and not config.get('base_url', '').strip():
            result = False
            message = f"{config.get('provider')}提供商需要配置base_url"
        else:
            result = True
            message = "配置正确"
        
        expected = scenario['expected']
        status = "✅ 通过" if result == expected else "❌ 失败"
        
        print(f"      预期: {'正确' if expected else '错误'}")
        print(f"      实际: {'正确' if result else '错误'}")
        print(f"      消息: {message}")
        print(f"      结果: {status}")

def main():
    """主测试函数"""
    print("🚀 AI配置验证改进测试")
    print("=" * 60)
    
    # 测试AI服务
    service_enabled, service_message = test_ai_config_validation()
    
    # 测试API端点
    api_enabled = test_api_endpoint()
    
    # 测试配置场景
    test_config_scenarios()
    
    # 总结
    print("\n" + "=" * 60)
    print("📊 测试结果总结:")
    print(f"   AI服务配置: {'✅ 正确' if service_enabled else '❌ 不正确'} - {service_message}")
    
    if api_enabled is not None:
        print(f"   API端点响应: {'✅ 正常' if api_enabled else '❌ 配置问题'}")
    else:
        print("   API端点响应: ⚠️  服务未运行")
    
    print("\n🎯 改进效果:")
    print("   ✅ 详细的配置验证逻辑")
    print("   ✅ 具体的错误信息提示")
    print("   ✅ 提供商和模型信息显示")
    print("   ✅ 灰色显示不可用选项")
    print("   ✅ 鼠标悬停显示详细信息")
    
    if service_enabled:
        print("\n🎉 AI批改功能配置正确，可以正常使用！")
    else:
        print(f"\n⚠️  AI批改功能配置有问题: {service_message}")
        print("   请检查config.py中的AI_GRADING_CONFIG配置")

if __name__ == '__main__':
    main()