# 需求
1. 把obsidian文章导入博客文件夹，一键更新和发布。
1. 实现解析tag和Excerpt，自动生成Front-Matter。【因为在obsidian写文章时不想写Front-Matter，很麻烦呀】
2. 版本控制，实现自己和博客发布双版本。【其实就是删除包含敏感信息的文本块】
3. 博客仓库md文件和图片文件解耦。所有图片存放到img文件夹下不同文件夹，md文件夹内只有所有md文件。【图片放在一起好管理】

# QuickStart 如何使用
1. 在本目录中新建 `HEXO_DB.yml`，并且写入Obsidian Vault的根目录和Hexo博客的source目录。
	```
	A_HEXO_SOURCE_DIR: /Users/xxx/hexoblog/source
	A_OBSIDIAN_VAULT_DIR: /Users/xxx/obsidian/Documents/VaultName
	```
2. 修改 `moveMarkdowns.sh` 中的hexo_dir，它是 `A_HEXO_SOURCE_DIR` 的上级目录。
3. `bash moveMarkdowns.sh` 自动将文章和图片从Obsidian复制到Hexo博客，然后push源码到github。
4. 如果有不想脚本处理的md文件，或者脚本碰到总是出错的md文件想跳过，在 `HEXO_DB.yml` 中添加`IGNORE_MARKDOWN_FILES` 列表

	```
	IGNORE_MARKDOWN_FILES: 
	  - example{{date}}.md
	```


# 设计
> front-matter里的tags和正文 `#xxx` 的tags都一样可以被obsidian识别。我们这里引入一个人为强假设：我所有的正文tag只写在第一行！

1. Obsidian中md增加YAML：运行add-front-matter.py，在obsidian中尝试读取所有文件的FrontMatter的tags，并且解析第一行可能存在的tags，对所有包含“blog”标签的markdown文件，自动去除第一行tags，生成FrontMatter，并保存到obsidian文件夹中。计算每个md的hash。
2. 将Obsidian中需要的md文章和涉及图片复制到hexo blog source目录：运行copy-to-hexo.py读取HEXO_DB.yml缓存，跳过缓存中所有存在且hash没变化的文章。
	1. 删除“blog”标签。因为复制过来的所有文章都有这个标签
	2. 预处理策略，去掉敏感信息文本块 `> [!Danger]` 块，大小写不敏感
	3. 检查引用的url
		1. http链接，则保留该url
		2. 引用md和pdf则去掉链接格式，只保留该文件名【TODO：双链文章如果在博客缓存中出现，则改为网页url】
		3. 本地图片存在则转移到hexo img dir
3. 复制完成后，缓存更新该文件原文的hash。
4. 博客自动将源码add, commit, push。 Github Actions自动部署到github.io博客网站。

# 更多
更多细节请看我的[个人博客文章](https://mediocrityxt.github.io/blogsite/2024/%E6%9B%B4%E6%96%B0%E5%8D%9A%E5%AE%A2/)