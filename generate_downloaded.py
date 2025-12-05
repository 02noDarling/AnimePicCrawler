import os
import re

def extract_post_ids_from_images(root_dir, output_file='downloaded.txt'):
    """
    遍历 root_dir 目录及其子目录，提取所有图片文件名中的 post_id，
    并写入 output_file 文件中（每行一个 ID）。
    """

    # 支持的图片扩展名（可按需扩展）
    image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.tiff'}

    post_ids = set()  # 使用 set 避免重复

    for dirpath, _, filenames in os.walk(root_dir):
        print(f"正在检查目录: {dirpath}")  # 调试信息
        for filename in filenames:
            print(f"找到文件: {filename}")  # 调试信息
            _, ext = os.path.splitext(filename)
            if ext.lower() in image_extensions:
                # 尝试匹配 post_id：在文件名中找形如 "ANIME-PICTURES.NET_-_<post_id>-" 的模式
                match = re.search(r'ANIME-PICTURES\.NET_-_(\d+)-', filename)
                if match:
                    post_id = match.group(1)
                    post_ids.add(post_id)
                    print(f"从文件 {filename} 提取到 post_id: {post_id}")  # 调试信息
                else:
                    print(f"未能从文件 {filename} 中提取 post_id.")  # 调试信息

    # 写入文件
    with open(output_file, 'w', encoding='utf-8') as f:
        for pid in sorted(post_ids, key=int):  # 按数字大小排序（可选）
            f.write(pid + '\n')

    print(f"成功提取 {len(post_ids)} 个唯一 post_id，已写入 {output_file}")

# 使用示例：
extract_post_ids_from_images(r'D:\VsCodeProjects\Dataset\2Dimages')