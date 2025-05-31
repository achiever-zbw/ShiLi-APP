# ⏳ 时砾 - 时间管理与任务协作系统

**时砾（TimeGrit）**，寓意时间如沙砾，珍惜每一粒。  
这是一个基于 Flask 构建的轻量级任务管理系统，支持任务安排、笔记记录、评论互动等功能，适用于日常学习计划管理与记录。

---

## ⚡️ 快速体验
- 访问  [时砾任务](http://power-sci.com.cn) (点击链接即可使用)

---

## 🚀 项目亮点

- ✅ 任务清单管理（增删改查）
- 📝 个人笔记模块（支持富文本编辑）
- 💬 评论模块（任务和笔记的交流与反馈）
- 🌐 前后端分离架构，支持跨域访问
- 🔒 安全性考虑：JWT Token 验证、输入校验、错误处理、数据库防注入
- 📅 日期时间安排：任务计划具体到日期、时间，方便精细化管理

---

## 🛠️ 技术栈选择

### 后端技术
- **框架** ： Flask，轻量级基于Python的Web框架，适合本项目的快速开发
- **语言** ： Python
- **数据库** ： MySQL 关系型数据库，方便管理与维护
- **认证** ： JWT Token 安全的用户身份验证方式

### 前端技术
- **框架** ： 原生 HTML/CSS/JavaScript 简洁灵活，轻量级

---

## 📁 项目结构

```
时砾APP/
|————frontend/                        # 前端文件
     |————images/                     # 图片集合
     |————comment.html                # 评论界面
     |————forget.html                 # 忘记密码界面
     |————...
|————routes/                          # 后端路由
|————app.py                           # Flask应用启动
|————config.py                        # 配置文件
|————db.py                            # 数据库连接
|————requirements.txt                 # 依赖包列表
```

---
## 📋 功能说明

### 1. 任务管理
- 添加任务：支持设置任务名称、描述、截止日期、状态
- 查看任务：列表展示所有任务
- 编辑任务：修改任务信息
- 删除任务：移除已完成或不再需要的任务

<p align="center">
  <img src="show_images/task/task1.png" width="600"/>
  <img src="show_images/task/task2.png" width="600"/>
</p>


### 2. 笔记功能
- 创建笔记：支持富文本编辑
- 书写内容：随时记录

<p align="center">
  <img src="show_images/note/note1.png" width="600"/>
  <img src="show_images/note/note2.png" width="600"/>
</p>

### 3. 评论系统
- 论坛开放：所有用户均可在论坛区发表评论并删除

<p align="center">
  <img src="show_images/comment/comment.png" width="600"/>
</p>

---
## 💡 提示说明

- **前端配置提示**  
  在 `frontend` 文件夹中的 HTML 文件（如 `task.html`, `note.html` 等）中，所有涉及后端 API 调用的部分，已将原始服务器 IP 地址统一替换为占位符 `my_ip`。  
  > 🔧 请根据你的部署环境，将 `my_ip` 替换为实际服务器的 IP 地址或域名（例如：`http://127.0.0.1:5000` 或 `http://your-domain.com`）。

- **后端配置提示**  
  在 `config.py` 文件中，以下数据库配置项已设置为占位符值，便于自定义：
  - 数据库密码：`mysql_password`  
  - 数据库名称：`my_database`  
  > 🔐 部署前请根据你本地或远程 MySQL 的实际配置，修改为正确的用户名、密码及数据库名称，以确保后端可以成功连接数据库。

- **建议操作**  
  - 修改完毕后，记得重启 Flask 服务使配置生效；
  - 若项目部署至公网，建议避免在配置文件中暴露真实密码，可使用环境变量或配置文件分离策略。
