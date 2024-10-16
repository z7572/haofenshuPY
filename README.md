# 坏  分  数 | haofenshuPY
<p align="center">
  <a href="https://github.com/z7572/haofenshuPY/releases/latest">
    <img src="https://img.shields.io/github/downloads/z7572/haofenshuPY/total?label=Github%20downloads&logo=github">
  </a>
</p>

## 简介

一个好分数查分程序，包括基于wxpython的GUI版本(Windows) 和纯命令行版本(手机)

> [!NOTE]
> 因为好分数的网页版和客户端会因学校设置屏蔽一些内容，而且没有会员看不到大量信息
> 
> 但是，网络发送的请求api包括更多信息，可以通过抓包来查看，但这样还是不太方便
> 
> so，我编写了这个程序，通过使用好分数的api发送请求并解析，直观地显示信息

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
    - 班/级平均分
    - 班/级最高分
- 查看答题卡（右键所选科目）

（后续会增加单个账号切换绑定学生的功能）

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

>本项目使用 `auto-py-to-exe` 打包 [*](https://blog.csdn.net/qq_40836442/article/details/139061604)

无需配置环境，下载[releases](https://github.com/z7572/haofenshuPY/releases/)中的exe文件并运行即可
