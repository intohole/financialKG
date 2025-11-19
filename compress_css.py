import re

# 读取CSS文件
with open('kg/static/css/styles.css', 'r') as f:
    css_content = f.read()

# 删除CSS注释
compressed_css = re.sub(r'\/\*[\s\S]*?\*\/', '', css_content)

# 删除多余的空白
compressed_css = re.sub(r'\s+', ' ', compressed_css)
compressed_css = re.sub(r'\s*([{}:;])\s*', r'\1', compressed_css)

# 保存压缩后的CSS文件
with open('kg/static/css/styles.min.css', 'w') as f:
    f.write(compressed_css)

print(f'CSS压缩完成！原始大小: {len(css_content)} 字节')
print(f'压缩后大小: {len(compressed_css)} 字节')
print(f'压缩率: {round((1 - len(compressed_css)/len(css_content))*100, 2)}%')