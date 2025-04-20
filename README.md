# OhMyPhoto - Open Source Photo Viewer


**⚠️ Development Status: This project is currently under active development and is not yet ready for production use. Features are incomplete and may change.**

**License:** This project is licensed under the [GNU General Public License v3.0](https://www.gnu.org/licenses/gpl-3.0.en.html).

---

## English

OhMyPhoto aims to be a web-based open source photo viewer.

### Planned Features

* Complete user account system
* Web interface for browsing photos (timeline view)
* View and edit EXIF metadata
* Separate storage for thumbnails and metadata (Docker-friendly)
* Text-based image search
* Pluggable face recognition module
* Pluggable scene recognition module
* Pluggable OCR module

### Current Status

The basic backend structure is set up using Flask, including:

* User authentication (registration, login, logout)
* Database models for Users and Photos (using SQLite and Flask-SQLAlchemy/Migrate)
* A photo library scanner (`flask scan-library`) to index images, extract basic metadata/timestamps, and generate thumbnails.
* Basic web routes for login, registration, and a simple timeline view (displaying thumbnails).

### Getting Started (Development)

1. Clone the repository.
2. Set up a Python environment (e.g., using `conda` or `venv`).
3. Install dependencies: `pip install -r requirements.txt`
4. Initialize/Upgrade the database:
   * `set FLASK_APP=run.py` (or `export FLASK_APP=run.py` on Linux/macOS)
   * `flask db init` (only first time)
   * `flask db migrate -m "Initial migration"`
   * `flask db upgrade`
5. Place image files into the `photo_library` directory (it will be created if it doesn't exist).
6. Run the library scanner: `flask scan-library`
7. Run the development server: `python run.py`
8. Access the application at `http://localhost:5000`.

---

## 中文 (Chinese)

OhMyPhoto的目标是成为一个基于 Web 的开源照片查看器。

### 计划中的功能

* 完整的用户账户系统
* 用于浏览照片的 Web 界面（时间轴视图）
* 查看和编辑 EXIF 元数据
* 缩略图和元数据的独立存储空间（便于 Docker 容器化）
* 基于文本的图像搜索（文搜图）
* 可插拔的人脸识别模块
* 可插拔的场景识别模块
* 可插拔的 OCR 模块

### 当前状态

基础的后端结构已使用 Flask 搭建完成，包括：

* 用户认证（注册、登录、登出）
* 用户和照片的数据库模型（使用 SQLite 和 Flask-SQLAlchemy/Migrate）
* 一个照片库扫描器 (`flask scan-library`)，用于索引图片、提取基本元数据/时间戳并生成缩略图。
* 用于登录、注册和简单时间轴视图（显示缩略图）的基本 Web 路由。

### 开始使用 (开发)

1. 克隆此仓库。
2. 设置 Python 环境 (例如, 使用 `conda` 或 `venv`)。
3. 安装依赖: `pip install -r requirements.txt`
4. 初始化/更新数据库:
   * `set FLASK_APP=run.py` (Windows) 或 `export FLASK_APP=run.py` (Linux/macOS)
   * `flask db init` (仅首次需要)
   * `flask db migrate -m "Initial migration"`
   * `flask db upgrade`
5. 将图片文件放入 `photo_library` 目录 (如果目录不存在，脚本会自动创建)。
6. 运行照片库扫描器: `flask scan-library`
7. 运行开发服务器: `python run.py`
8. 在浏览器中访问 `http://localhost:5000`。
