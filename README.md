# 坏  分  数 | haofenshuPY

## 简介

基于wxpython的一个好分数查分用户界面

对比于网页版及客户端，该程序可以无视学校屏蔽，获取更多可以获得的考试信息

## 功能

运行时，程序会在当前目录下生成一个名为`config.json`的配置文件，用于存储学生姓名和token

- 多用户选择
- 查成绩
- 查考试信息
- 查排名
- 查平均、最高分

（后续会增加单个账号切换绑定学生的功能）

# 使用

## 直接运行

需要Python环境
``` 
pip install requests wxpython
python main.py
```

## 使用打包后的版本

> 本项目使用 [`auto-py-to-exe`](https://blog.csdn.net/qq_40836442/article/details/139061604 "参考资料") 打包

无需配置环境，下载[release](https://github.com/z7572/haofenshuPY/releases/)中的exe文件并运行即可