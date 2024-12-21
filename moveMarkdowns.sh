pip install termcolor python-frontmatter
cd /Users/xxx/Documents/Code/Obsidian2HexoSource/
python copy_to_hexo.py
msg="从Obsidian自动更新 $? 篇md文章 $(date -I)"
hexo_dir=/Users/xxx/Desktop/nextblog/
cd $hexo_dir && hexo clean && git add . && git commit -m "$msg" && git push
# hexo clean && hexo g && hexo s -o