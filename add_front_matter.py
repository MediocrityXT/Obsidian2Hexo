# https://github.com/eyeseast/python-frontmatter
import frontmatter
import os
import re
import datetime
import traceback
from termcolor import cprint
import hashlib

def hashPost(post):
    # md5 hash
    data = frontmatter.dumps(post)
    md5_obj = hashlib.md5()
    md5_obj.update(data.encode())
    md5_hash = md5_obj.hexdigest()
    return md5_hash

def getTags(text):
    # 使用正则表达式匹配第一行，并检查每个单词是否都符合要求
    lines = text.splitlines()
    words = lines[0].split()
    if len(words)>0 and all(re.match(r'#([\u4e00-\u9fffA-Za-z0-9]+)', word) for word in words):
        tags = [word.removeprefix('#') for word in words]
        return True, tags, '\n'.join(lines[1:]).strip()
    else:
        return False, [], text.strip()

def writePost2md(post, filepath):
    try:
        with open(filepath,'w') as f:
            f.write(frontmatter.dumps(post,sort_keys=False))
        return True
    except Exception as e:
        return False

def main(obsidian_vault_dir, ignore_markdown_files = []):
    success = {}
    failure = {}

    for dirpath,dirs,files in os.walk(obsidian_vault_dir):
        for file in files:
            if file.endswith('.md'):
                if file in ignore_markdown_files:
                    continue
                filepath = os.path.join(dirpath,file)
                try:
                    post = frontmatter.load(filepath)
                    tags = post.get('tags',[])
                    if not tags:
                        tags = []
                    if isinstance(tags, str):
                        tags = [tags]
                    assert isinstance(tags, list), TypeError(f"Wrong type of tags: {type(tags)} in {tags}")
                    # 检测第一行tags，如果有则读取，并删除第一行
                    haveFirstLineTags, firse_line_tags, text = getTags(post.content.strip())
                    tags = tags + firse_line_tags

                    # 只针对包含blog tag的markdown文件进行YAML重写
                    if 'blog' in tags:
                        title = post.get('title', file.removesuffix('.md'))
                        
                        excerpt = post.get('excerpt', '')
                        math = post.get('math', '')
                        if math != True:
                            math = False
                        # 如果文件存在date字段， 则使用该date，否则获取文件的创建时间戳， 将时间戳转换为日期时间
                        timestamp = os.stat(filepath).st_birthtime
                        created_date = post.get('date', datetime.datetime.fromtimestamp(timestamp).isoformat(sep=' ', timespec='seconds'))
                        post.metadata = {'title':title, 'date':created_date, 'math':math, 'excerpt':excerpt, 'tags':tags}
                        post.content = text
                        print(post.metadata)
                        hash_value = hashPost(post)
                        if not writePost2md(post,filepath):
                            failure[filepath]=f'\nWRITE ERROR: {filepath}'
                        else:
                            success[filepath] = hash_value

                except:
                    failure[filepath]=traceback.format_exc()


    cprint(f"Success:{len(success)},{success}", 'green')
    cprint(f"Failure:{len(failure)},{failure}", 'red')
    return success, failure

if __name__ == '__main__':
    main()