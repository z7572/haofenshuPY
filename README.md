## v3api失效，v4api解析中

# 坏  分  数 | haofenshuPY
<p align="center">
  <a href="https://github.com/z7572/haofenshuPY/releases/latest">
    <img src="https://img.shields.io/github/downloads/z7572/haofenshuPY/total?label=Github%20downloads&logo=github">
  </a>
</p>

## 简介

一个好分数查分程序，包括基于wxpython的GUI版本(Windows) 和纯命令行版本(手机)


## 功能

> [!TIP]
> 运行时，程序会在当前目录下生成一个名为`config.json`的配置文件，用于存储学生姓名和token

### GUI版本
- 记住密码与多用户选择
- 显示考试列表
    - 新增使用导出错题api，支持查看历史以来所有的考试（不止5次）
    - ~~*别告诉我你一道题都没错过*~~
- 查询（支持总成绩和单科）
    - 分数
    - 班/级排名
    ~~- 班/级平均分~~
    ~~- 班/级最高分~~
- 查看答题卡（右键所选科目）

~~（后续会增加单个账号切换绑定学生的功能）~~

### 命令行版本
- 以上除 查看答题卡 外的所有功能
- 导出结果至文件

## 使用

### 直接运行

需要Python环境
``` 
pip install -r requirements.txt
```
运行`main.py`或`main-no-GUI.py`

### 使用打包后的版本

无需配置环境，下载[releases](https://github.com/z7572/haofenshuPY/releases/)中的exe文件并运行
