# 课堂测试系统调试设计文档

## 概述

本文档描述了课堂测试系统的调试和改进设计。系统基于 Flask 框架，使用 SQLAlchemy ORM 进行数据库操作，支持教师端的题库管理和学生端的在线测试功能。

主要改进目标：
1. 完善数据库初始化流程
2. 增强题库导入功能的健壮性
3. 改进测试配置管理
4. 优化学生测试流程
5. 增强成绩统计功能
6. 完善简答题人工批改功能
7. 新增学生历史答题查看功能
8. 改进错误处理和用户体验
9. 统一时区处理

## 架构

系统采用经典的 MVC 架构：

### 模型层 (Model)
- 使用 SQLAlchemy ORM 定义数据模型
- 主要模型：User, QuestionBank, Question, Test, TestResult, TestPreset, ShortAnswerSubmission, StudentTestHistory

### 视图层 (View)
- 使用 Jinja2 模板引擎
- 模板文件位于 templates/ 目录
- 静态资源位于 static/ 目录

### 控制层 (Controller)
- Flask 路由处理请求
- 业务逻辑在路由函数中实现
- API 端点提供 JSON 响应

### 数据流
```
用户请求 → Flask 路由 → 业务逻辑 → 数据库操作 → 响应渲染 → 返回用户
```

## 组件和接口

### 1. 数据库初始化模块

**功能**: 负责系统首次启动时的数据库初始化

**接口**:
```python
def init_db():
    """初始化数据库，创建所有表和默认数据"""
    with app.app_context():
        db.create_all()
        # 创建默认教师账户
        if not User.query.filter_by(username='admin', role='teacher').first():
            admin = User(username='admin', role='teacher')
            admin.set_password('admin')
            db.session.add(admin)
            db.session.commit()
```

**改进点**:
- 添加错误处理和日志记录
- 检查数据库连接状态
- 提供初始化状态反馈

### 2. 题库导入模块

**功能**: 处理 CSV 和 Excel 格式的题库文件导入

**接口**:
```python
@app.route('/import_questions/<question_type>', methods=['POST'])
def import_questions(question_type):
    """导入题库文件"""
    # 文件验证
    # 格式解析
    # 数据验证
    # 批量插入
    # 返回结果
```

**列名映射规范**:

根据题库目录下的模板文件，不同题型要求的列名如下：

1. **单选题 (single_choice)**:
   - 必需列: 题干、选项A、选项B、选项C、选项D、正确答案、分值、答案解析

2. **多选题 (multiple_choice)**:
   - 必需列: 题干、选项A、选项B、选项C、选项D、选项E、正确答案、分值、解析

3. **判断题 (true_false)**:
   - 必需列: 题干、正确答案、分值、解析

4. **填空题 (fill_blank)**:
   - 必需列: 题干、正确答案、分值、解析

5. **简答题 (short_answer)**:
   - 必需列: 题目内容、参考答案、分值、解析

**列名验证逻辑**:
```python
REQUIRED_COLUMNS = {
    'single_choice': ['题干', '选项A', '选项B', '选项C', '选项D', '正确答案', '分值', '答案解析'],
    'multiple_choice': ['题干', '选项A', '选项B', '选项C', '选项D', '选项E', '正确答案', '分值', '解析'],
    'true_false': ['题干', '正确答案', '分值', '解析'],
    'fill_blank': ['题干', '正确答案', '分值', '解析'],
    'short_answer': ['题目内容', '参考答案', '分值', '解析']
}

def validate_columns(df, question_type):
    """验证文件列名是否符合题型要求"""
    required = REQUIRED_COLUMNS.get(question_type, [])
    missing = [col for col in required if col not in df.columns]
    if missing:
        return False, f"缺少必需列: {', '.join(missing)}"
    return True, "列名验证通过"
```

**改进点**:
- 增强文件格式验证
- 为每种题型定义专门的列名要求
- 改进错误信息提示，明确指出缺失的列名
- 添加导入进度反馈
- 支持事务回滚

### 3. 测试配置模块

**功能**: 管理测试参数配置和预设

**接口**:
```python
@app.route('/save_test_settings', methods=['POST'])
def save_test_settings():
    """保存测试配置"""
    # 参数验证
    # 题库验证
    # 计算总分
    # 自动保存为预设（使用测试标题作为预设名）
    # 返回预设ID

@app.route('/api/test_presets', methods=['GET'])
def get_test_presets():
    """获取所有预设列表"""
    # 返回预设列表

@app.route('/api/test_presets/<int:preset_id>', methods=['GET'])
def get_test_preset(preset_id):
    """获取指定预设的详细配置"""
    # 返回预设配置

@app.route('/api/test_presets/<int:preset_id>', methods=['DELETE'])
def delete_test_preset(preset_id):
    """删除指定预设"""
    # 删除预设
    # 返回成功状态
```

**改进点**:
- 添加必填字段验证
- 验证题库题目数量
- 自动计算总分
- 简化预设保存流程：移除"保存为预设"复选框，直接使用测试标题作为预设名
- 在预设下拉列表旁添加删除按钮
- 智能控制删除按钮状态（选择预设时启用，否则禁用）
- 删除预设后自动刷新预设列表

### 4. 学生测试模块

**功能**: 处理学生测试流程

**接口**:
```python
@app.route('/test')
def test():
    """生成测试题目"""
    # 获取配置
    # 随机抽题
    # 渲染测试页面

@app.route('/submit_test', methods=['POST'])
def submit_test():
    """提交测试答案"""
    # 收集答案
    # 自动评分
    # 保存结果
    # 更新统计
```

**改进点**:
- 支持预设选择
- 改进答案保存逻辑
- 优化评分算法
- 处理图片上传

### 5. 成绩统计模块

**功能**: 提供测试成绩统计和分析

**接口**:
```python
@app.route('/test_statistics')
def test_statistics():
    """显示所有测试统计"""

@app.route('/test_statistics/<int:test_id>')
def get_test_statistics(test_id):
    """显示特定测试的详细统计"""
    # 班级统计
    # 学生成绩明细
    # 错题统计
```

**改进点**:
- 优化统计计算性能
- 增加错题分析
- 改进数据展示

### 6. 简答题批改模块

**功能**: 支持教师对简答题进行人工批改

**接口**:
```python
@app.route('/grade_short_answer_by_result', methods=['POST'])
def grade_short_answer_by_result():
    """批改简答题"""
    # 保存评分和评语
    # 重新计算总分
    # 更新历史统计
```

**改进点**:
- 在答题详情页面直接批改
- 实时更新总分
- 同步更新历史统计
- 显示批改状态

### 7. 学生历史查看模块

**功能**: 允许学生查看历次测试的答题详情

**接口**:
```python
@app.route('/student_dashboard')
def student_dashboard():
    """学生面板，显示历史记录"""

@app.route('/test_result/<int:result_id>')
def test_result(result_id):
    """显示测试答题详情"""
    # 权限验证
    # 获取答题数据
    # 展示详细信息
```

**改进点**:
- 新增历史记录列表
- 支持查看每次测试详情
- 显示正确答案和解析
- 区分正确和错误答案

### 8. 时区处理模块

**功能**: 统一处理时间的存储和显示

**接口**:
```python
def to_bj(dt: datetime):
    """将 UTC 时间转换为北京时间"""
    return (dt + BJ_OFFSET) if dt else dt

def bjtime_filter(value, fmt='%Y-%m-%d %H:%M'):
    """Jinja2 过滤器，格式化北京时间"""
    if not value:
        return ''
    return to_bj(value).strftime(fmt)
```

**改进点**:
- 统一使用 UTC 存储
- 显示时转换为北京时间
- 使用 Jinja2 过滤器
- 处理空值情况

## 数据模型

### User (用户)
```python
class User(db.Model):
    id: Integer (主键)
    username: String(80) (唯一)
    password_hash: String(128)
    role: String(20)  # 'teacher' or 'student'
```

### QuestionBank (题库)
```python
class QuestionBank(db.Model):
    id: Integer (主键)
    name: String(100)
    question_type: String(20)
    created_at: DateTime
    questions: Relationship (一对多)
```

### Question (题目)
```python
class Question(db.Model):
    id: Integer (主键)
    question_type: String(20)
    content: Text
    image_path: String(200)
    option_a/b/c/d/e: String(200)
    correct_answer: String(200)
    score: Integer
    explanation: Text
    created_at: DateTime
    bank_id: Integer (外键)
```

### Test (测试配置)
```python
class Test(db.Model):
    id: Integer (主键)
    title: String(200)
    *_count: Integer  # 各题型数量
    *_score: Integer  # 各题型分值
    *_bank_id: Integer  # 各题型题库ID
    total_score: Integer
    is_active: Boolean
    allow_student_choice: Boolean
    created_at: DateTime
```

### TestResult (测试结果)
```python
class TestResult(db.Model):
    id: Integer (主键)
    student_id: Integer (外键)
    student_name: String(100)
    class_number: String(50)
    test_id: Integer (外键)
    score: Integer
    answers: Text (JSON)
    ip_address: String(15)
    created_at: DateTime
```

### TestPreset (测试预设)
```python
class TestPreset(db.Model):
    id: Integer (主键)
    title: String(100)
    # 与 Test 相同的配置字段
    created_at: DateTime
```

### ShortAnswerSubmission (简答题提交)
```python
class ShortAnswerSubmission(db.Model):
    id: Integer (主键)
    result_id: Integer (外键)
    question_id: Integer (外键)
    student_answer: Text
    image_path: String(200)
    score: Integer (可空)
    comment: Text (可空)
    graded_bool: Boolean
    created_at: DateTime
```

### StudentTestHistory (学生测试历史)
```python
class StudentTestHistory(db.Model):
    id: Integer (主键)
    student_id: Integer (外键)
    student_name: String(100)
    class_number: String(50)
    test_count: Integer
    total_score: Integer
    average_score: Float
    highest_score: Integer
    lowest_score: Integer
    updated_at: DateTime
```

## 正确性属性

*属性是一个特征或行为，应该在系统的所有有效执行中保持为真——本质上是关于系统应该做什么的正式声明。属性作为人类可读规范和机器可验证正确性保证之间的桥梁。*


### 属性 1: 数据库初始化幂等性
*对于任何*系统状态，多次运行数据库初始化不应该创建重复的数据或改变已存在的数据
**验证: 需求 1.3**

### 属性 2: CSV 文件解析正确性
*对于任何*符合格式要求的 UTF-8 编码 CSV 文件，解析后的题目数量应该等于文件中的数据行数
**验证: 需求 2.1, 2.4**

### 属性 3: Excel 文件解析正确性
*对于任何*符合格式要求的 .xlsx 文件，解析后的题目数量应该等于文件中的数据行数
**验证: 需求 2.2, 2.4**

### 属性 4: 文件导入错误处理
*对于任何*格式不正确的文件，系统应该返回包含具体错误信息的响应，而不是抛出未捕获的异常
**验证: 需求 2.3**

### 属性 5: 图片路径存储往返一致性
*对于任何*包含图片路径的题目，存储到数据库后再读取，应该得到相同的图片路径
**验证: 需求 2.5**

### 属性 6: 测试配置必填字段验证
*对于任何*缺少必填字段的测试配置，系统应该拒绝保存并返回验证错误
**验证: 需求 3.1**

### 属性 7: 题库题目数量验证
*对于任何*测试配置，如果某题型要求的题目数量超过对应题库中的可用题目数量，系统应该拒绝该配置
**验证: 需求 3.2**

### 属性 8: 测试总分自动计算
*对于任何*测试配置，总分应该等于所有题型的（题目数量 × 单题分值）之和
**验证: 需求 3.3**

### 属性 9: 测试预设往返一致性
*对于任何*测试预设，保存后再读取，应该得到相同的配置参数
**验证: 需求 3.4, 3.6**

### 属性 9a: 预设自动保存使用测试标题
*对于任何*测试配置保存操作，系统应该自动创建一个预设，其名称等于测试标题
**验证: 需求 3.4**

### 属性 9b: 预设列表包含新保存的预设
*对于任何*新保存的预设，在预设列表中应该能够找到该预设
**验证: 需求 3.5**

### 属性 9c: 删除预设后列表不包含该预设
*对于任何*被删除的预设，删除后在预设列表中不应该再出现
**验证: 需求 3.8**

### 属性 10: 学生账户自动创建或登录
*对于任何*姓名和班级号组合，系统应该能够创建新账户或找到已存在的账户，不应该创建重复账户
**验证: 需求 4.1**

### 属性 11: 随机抽题数量和来源正确性
*对于任何*测试配置，抽取的题目数量应该等于配置的数量，且所有题目都来自指定的题库
**验证: 需求 4.2**

### 属性 12: 答案保存往返一致性
*对于任何*学生提交的答案，保存到数据库后再读取，应该得到相同的答案内容
**验证: 需求 4.3**

### 属性 13: 自动评分正确性
*对于任何*提交的测试答案，自动评分的结果应该等于所有正确答案的分值之和
**验证: 需求 4.4**

### 属性 14: 图片上传关联正确性
*对于任何*简答题的图片上传，图片应该正确关联到对应的答案记录
**验证: 需求 4.5**

### 属性 15: 班级统计计算正确性
*对于任何*一组测试成绩，计算的平均分应该等于总分除以人数，最高分和最低分应该是集合中的实际值，及格率应该等于及格人数除以总人数
**验证: 需求 5.3**

### 属性 16: 错题排序正确性
*对于任何*错题统计结果，返回的题目应该按错误率降序排列，且数量不超过10道
**验证: 需求 5.4**

### 属性 17: 答题详情完整性
*对于任何*测试结果，答题详情应该包含所有题目的完整信息（题目、学生答案、正确答案、得分）
**验证: 需求 5.5, 8.3**

### 属性 18: 简答题评分范围验证
*对于任何*简答题评分，如果分数超出有效范围（0到题目满分），系统应该拒绝该评分
**验证: 需求 6.3**

### 属性 19: 简答题评分往返一致性
*对于任何*简答题评分，保存后立即查询应该得到相同的分数和评语
**验证: 需求 6.4**

### 属性 20: 简答题评分后总分重算正确性
*对于任何*包含简答题的测试，批改简答题后重新计算的总分应该等于所有题目得分之和
**验证: 需求 6.5**

### 属性 21: 总分更新后历史统计同步
*对于任何*学生的测试总分更新，历史统计数据（平均分、最高分、最低分）应该基于所有测试结果重新计算
**验证: 需求 6.6**

### 属性 22: 简答题批改状态显示
*对于任何*简答题，如果未批改（score 为 NULL），应该显示"待批改"状态；如果已批改，应该显示分数和评语
**验证: 需求 6.9, 8.6, 8.7**

### 属性 23: 多简答题批改总分实时更新
*对于任何*包含多个简答题的测试，每批改一题后，总分应该立即更新为当前所有已评分题目的得分之和
**验证: 需求 6.10**

### 属性 24: 输入验证错误信息明确性
*对于任何*无效输入，系统应该返回包含具体验证错误信息的响应，而不是通用错误
**验证: 需求 7.2**

### 属性 25: 文件上传错误提示明确性
*对于任何*文件上传失败的情况，系统应该返回包含失败原因（格式、大小等）的错误信息
**验证: 需求 7.3**

### 属性 26: 未授权访问拒绝
*对于任何*需要特定权限的操作，如果用户权限不足，系统应该拒绝访问并返回权限错误
**验证: 需求 7.5**

### 属性 27: 测试记录时间排序
*对于任何*学生的测试记录列表，应该按创建时间降序排列（最新的在前）
**验证: 需求 8.8**

### 属性 28: 学生统计数据计算正确性
*对于任何*学生的所有测试记录，统计的总次数应该等于记录数量，平均分应该等于总分除以次数，最高分和最低分应该是实际值
**验证: 需求 8.9**

### 属性 29: 答案正确性视觉区分
*对于任何*答题详情展示，错误答案应该有明显的视觉标记（如红色）与正确答案（如绿色）区分
**验证: 需求 8.4**

### 属性 30: 题目解析条件显示
*对于任何*题目，如果有解析内容（explanation 不为空），应该在答题详情中显示；如果没有，不应该显示空的解析区域
**验证: 需求 8.5**

### 属性 31: 时间存储格式一致性
*对于任何*时间戳，存储到数据库时应该使用 UTC 时间格式
**验证: 需求 9.1**

### 属性 32: 时间显示转换正确性
*对于任何*从数据库读取的 UTC 时间，显示时应该转换为北京时间（UTC+8）
**验证: 需求 9.2**

### 属性 33: 时间格式化一致性
*对于任何*显示的时间，应该使用统一的格式字符串（默认为 '%Y-%m-%d %H:%M'）
**验证: 需求 9.3**

## 错误处理

### 数据库错误
- 使用 try-except 捕获数据库异常
- 发生错误时回滚事务
- 记录错误日志
- 向用户显示友好的错误信息

### 文件上传错误
- 验证文件类型和大小
- 检查文件编码
- 捕获解析异常
- 提供具体的错误提示

### 输入验证错误
- 前端和后端双重验证
- 返回具体的字段错误信息
- 保持用户已输入的数据

### 权限错误
- 检查用户登录状态
- 验证用户角色权限
- 重定向到适当的页面
- 显示权限不足提示

### 会话错误
- 检查会话有效性
- 会话过期时清理数据
- 重定向到登录页面

## 测试策略

### 单元测试
系统将使用 pytest 进行单元测试，重点测试：

1. **数据模型测试**
   - 测试模型的创建、更新、删除
   - 测试关系映射
   - 测试数据验证

2. **业务逻辑测试**
   - 测试评分算法
   - 测试统计计算
   - 测试数据转换

3. **工具函数测试**
   - 测试时间转换函数
   - 测试文件解析函数
   - 测试数据验证函数

### 属性测试
系统将使用 Hypothesis 进行属性测试，每个属性测试至少运行 100 次迭代。

**属性测试库**: Hypothesis (Python)

**测试标记格式**: 每个属性测试必须包含注释，格式为：
```python
# Feature: debug-test-system, Property X: [属性描述]
```

**关键属性测试**:
1. 数据往返一致性（配置、答案、评分）
2. 计算正确性（总分、统计数据）
3. 排序和过滤正确性
4. 输入验证完整性
5. 错误处理健壮性

### 集成测试
测试完整的用户流程：
1. 教师登录 → 导入题库 → 配置测试
2. 学生登录 → 参加测试 → 提交答案
3. 教师查看统计 → 批改简答题
4. 学生查看历史记录

### 测试数据生成
使用 Hypothesis 的策略生成测试数据：
- 随机用户信息
- 随机题目内容
- 随机测试配置
- 随机答案组合

## 性能考虑

### 数据库查询优化
- 使用索引加速常用查询
- 避免 N+1 查询问题
- 使用 eager loading 加载关联数据
- 对大量数据使用分页

### 缓存策略
- 缓存题库列表
- 缓存测试配置
- 使用 Flask-Caching

### 文件处理优化
- 限制上传文件大小
- 使用流式处理大文件
- 异步处理文件导入

## 安全考虑

### 认证和授权
- 使用 session 管理用户登录状态
- 密码使用 werkzeug.security 加密
- 检查用户角色权限

### 输入验证
- 验证所有用户输入
- 防止 SQL 注入（使用 ORM）
- 防止 XSS 攻击（模板自动转义）

### 文件上传安全
- 限制文件类型
- 限制文件大小
- 使用安全的文件名
- 存储在非执行目录

## 部署考虑

### 环境配置
- 使用环境变量管理敏感配置
- 区分开发和生产环境
- 使用 waitress 作为生产服务器

### 数据库迁移
- 支持从 SQLite 迁移到 MySQL/PostgreSQL
- 提供数据备份和恢复脚本

### 日志记录
- 记录关键操作日志
- 记录错误和异常
- 使用日志轮转

## 未来改进

1. **实时通知**: 使用 WebSocket 实现实时成绩更新
2. **批量操作**: 支持批量导入、批量批改
3. **数据导出**: 支持导出成绩报表
4. **题目编辑器**: 富文本编辑器支持
5. **移动端适配**: 响应式设计优化
6. **多语言支持**: 国际化和本地化
7. **API 接口**: 提供 RESTful API
8. **权限细化**: 更细粒度的权限控制
