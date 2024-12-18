import add_front_matter
import yaml
import os 
import re
import shutil
import sys
from termcolor import cprint
import frontmatter
SCRIPT_DIR = os.path.split(__file__)[0]
HEXO_DB_YAML = SCRIPT_DIR+'/HEXO_DB.yml'

def removeBlogTag(content):
    post = frontmatter.loads(content)
    tags = post.get('tags',[])
    tags.remove('blog')
    post['tags'] = tags
    return frontmatter.dumps(post, sort_keys=False)

def removeDangerCallout(content):
    # Define the regex pattern for danger blocks with case-insensitive flag
    pattern = re.compile(r'^> \[!DANGER\][^\n]*\n(?:> [^\n]*\n)*', re.MULTILINE | re.IGNORECASE)
    # Remove danger blocks from the content
    clean_content = pattern.sub('\n', content)
    return clean_content

def get_real_img_url(url, filedir, obsidian_vault_dir):
    # 1. 相对路径url，基于obsidian 根目录添加查找,
    # 2. 不含attachments则添加attachments再查找
    # 3. 相对路径url，基于filedir. 
    # 4. 不含attachments则添加attachments再查找
    # 5. 绝对路径url，基于obsidian根目录

    temp_urls = []
    if url.startswith('../'):
        temp_urls.append(os.path.join(filedir, url))
        temp_urls.append(os.path.join(filedir, 'attachments', url))
    elif url.startswith('./'):
        # url[2:]是去掉./前缀
        temp_urls.append(os.path.join(filedir, url[2:]))
        temp_urls.append(os.path.join(filedir, 'attachments', url[2:]))
        temp_urls.append(os.path.join(obsidian_vault_dir, url[2:]))
        temp_urls.append(os.path.join(obsidian_vault_dir, 'attachments', url[2:]))
    else:
        temp_urls.append(os.path.join(obsidian_vault_dir, url))
        temp_urls.append(os.path.join(obsidian_vault_dir, 'attachments', url))

    for u in temp_urls:
        if os.path.exists(u):
            return u

    raise FileNotFoundError(f'{url} not found')
    
def copy_and_replace_images(content, filedir, hexo_source_dir_img, filename_wo_ext, obsidian_vault_dir):
    # 替换函数，将匹配到的 URL 添加前缀
    def copy_and_replace_url(match):
        name = match.group(1)
        url = match.group(2)

        # http/https链接
        if url.startswith('http'):
            return f'![{name}]({url})'
        
        anchor = ''
        if '#' in url:
            assert len(url.split('#')) == 2, ValueError(f"{url} has more than one #")
            url, anchor_title = url.split('#')
            if anchor_title:
                anchor = f'#{anchor_title}'

        # 本地md或者pdf双链
        if url.endswith('.md') or url.endswith('.pdf'):
            return f'{os.path.split(url)[-1]}{anchor})'
        # 本地图片不应该包括Anchor
        else:
            try:
                # 根据obsidian规则自动尝试找到url对应图片的绝对路径
                # 但是最佳做法：用户写md时url都是相对路径

                # 注意url里空格是编码成%20，需要替换成空格才是本地路径。
                # 但是在博客md必须仍然是%20代替空格
                # ls: calculator%20-%20fcp.gif: No such file or directory
                local_url = url.replace('%20',' ')
                img_path = get_real_img_url(local_url, filedir, obsidian_vault_dir)
                img_name = os.path.split(img_path)[-1]
                os.makedirs(target_img_dir,exist_ok=True)
                shutil.copy(img_path, os.path.join(target_img_dir, img_name))
            except FileNotFoundError as e:
                cprint(f"[UrlNotFound] {filename}: {e}\n",'red')
                return f'![{name}]({url})'
            
            blog_img_url = f"/img/{filename_wo_ext}/{img_name}".replace(' ','%20')
            return f'![{name}]({blog_img_url})'

    #filedir: md file所在文件夹
    target_img_dir = os.path.join(hexo_source_dir_img, filename_wo_ext)

    # 获取所有本地图片链接
    # 正则表达式模式用于匹配 [name](url) 格式的链接
    # TODO：这里没有排除代码块``包裹的链接
    pattern = re.compile(r'!\[([^]]*)\]\(([^)]+)\)')
    # 使用 sub 方法进行替换
    modified_text = pattern.sub(copy_and_replace_url, content)
    
    return modified_text


if os.path.exists(HEXO_DB_YAML):
    with open(HEXO_DB_YAML, 'r') as f:
        hexo_db = yaml.load(f, Loader=yaml.FullLoader)
else:
    hexo_db = {'A_HEXO_SOURCE_DIR':input("A_HEXO_SOURCE_DIR:"),
               'A_OBSIDIAN_VAULT_DIR':input("A_OBSIDIAN_VAULT_DIR:")}
obsidian_vault_dir = hexo_db["A_OBSIDIAN_VAULT_DIR"]
hexo_source_dir = hexo_db['A_HEXO_SOURCE_DIR']
hexo_source_dir_img = os.path.join(hexo_source_dir, 'img')
hexo_source_dir_posts = os.path.join(hexo_source_dir, '_posts')

success,failure = add_front_matter.main(obsidian_vault_dir)

update_cnt = 0
for filepath, hash_value in success.items():
    filedir, filename = os.path.split(filepath)
    # hexo_db的key是file的相对路径
    # relative_filedir = os.path.relpath(filedir, obsidian_vault_dir)
    relative_filepath = os.path.relpath(filepath, obsidian_vault_dir)

    if not (relative_filepath in hexo_db and hexo_db[relative_filepath] == hash_value):
        filename_wo_ext = os.path.splitext(filename)[0]

        with open(filepath, 'r') as f:
            content = f.read()
        
        # 删除blog标签
        content = removeBlogTag(content)
        # 预处理，删除>[!Danger]段落
        content = removeDangerCallout(content)
        # 处理图片链接
        content = copy_and_replace_images(content, filedir, hexo_source_dir_img, filename_wo_ext, obsidian_vault_dir)

        os.makedirs(hexo_source_dir_posts,exist_ok=True)
        # 将多级文件夹所有文件都展平到同一层级
        target_filepath = os.path.join(hexo_source_dir_posts, filename)
        with open(target_filepath, 'w') as f:
            f.write(content)
        # copy完成， 保存hash_value到db，相当于缓存，这些有缓存的不用再更新和复制
        hexo_db[relative_filepath] = hash_value
        update_cnt += 1

with open(HEXO_DB_YAML, 'w') as f:
    yaml.dump(hexo_db, f, encoding='utf-8', allow_unicode=True)

# 返回更新的文件个数
sys.exit(update_cnt)