# -*- coding: utf-8 -*-
import os

# 获取当前文件所在目录
current_dir = os.path.dirname(os.path.abspath(__file__))
app_file = os.path.join(current_dir, 'app.py')

print(f"正在修复文件: {app_file}")

# 读取文件
with open(app_file, 'r', encoding='utf-8') as f:
    lines = f.readlines()

print(f"文件总行数: {len(lines)}")

# 检查第546-548行（索引545-547）
if len(lines) > 547:
    print(f"\n修复前的内容:")
    print(f"第546行 (索引545): {repr(lines[545])}")
    print(f"第547行 (索引546): {repr(lines[546])}")
    print(f"第548行 (索引547): {repr(lines[547])}")
    
    # 检查第546行是否是if语句
    if 'if not current_test:' in lines[545]:
        # 检查第547行是否需要修复
        if lines[546].startswith('        flash(') and not lines[546].startswith('            flash('):
            # 修复：添加4个空格
            original_547 = lines[546]
            original_548 = lines[547]
            
            lines[546] = '            ' + lines[546].lstrip()
            lines[547] = '            ' + lines[547].lstrip()
            
            print(f"\n修复后的内容:")
            print(f"第547行 (索引546): {repr(lines[546])}")
            print(f"第548行 (索引547): {repr(lines[547])}")
            
            # 写回文件
            with open(app_file, 'w', encoding='utf-8') as f:
                f.writelines(lines)
            
            print("\n✅ 修复成功！文件已保存。")
        else:
            print("\n第547行已经有正确的缩进，或者格式不匹配。")
            print(f"第547行的实际内容: {repr(lines[546])}")
    else:
        print("\n第546行不是预期的if语句。")
        print(f"第546行的实际内容: {repr(lines[545])}")
else:
    print(f"\n文件行数不足，只有{len(lines)}行。")

# 验证修复
print("\n验证修复结果:")
with open(app_file, 'r', encoding='utf-8') as f:
    lines = f.readlines()
    if len(lines) > 547:
        print(f"第547行: {repr(lines[546])}")
        if lines[546].startswith('            flash('):
            print("✅ 缩进正确（12个空格）")
        else:
            print(f"❌ 缩进不正确，实际缩进: {len(lines[546]) - len(lines[546].lstrip())}个空格")

