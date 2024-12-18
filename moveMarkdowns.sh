workdir=$(pwd)
hexo_dir=/Users/xxx/hexoblog/

python copy_to_hexo.py
msg="从Obsidian自动更新 $? 篇md文章 $(date -I)"
cd $hexo_dir
hexo clean
# hexo clean && hexo g && hexo s -o
git add . && git commit -m $msg
git push
cd $workdir
