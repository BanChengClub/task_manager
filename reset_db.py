#!/usr/bin/env python
import os
import sys
import django
from django.conf import settings

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'task_manager.settings')
django.setup()

from django.core.management import execute_from_command_line


def reset_database():
    """重置数据库"""
    # 删除数据库文件
    db_path = 'db.sqlite3'
    if os.path.exists(db_path):
        os.remove(db_path)
        print(f"已删除数据库文件: {db_path}")

    # 删除迁移文件
    migrations_dir = 'tasks/migrations'
    for filename in os.listdir(migrations_dir):
        if filename != '__init__.py':
            file_path = os.path.join(migrations_dir, filename)
            os.remove(file_path)
            print(f"已删除迁移文件: {file_path}")

    # 重新创建迁移
    print("创建迁移...")
    execute_from_command_line(['manage.py', 'makemigrations'])

    # 应用迁移
    print("应用迁移...")
    execute_from_command_line(['manage.py', 'migrate'])

    # 创建超级用户
    print("创建超级用户...")
    execute_from_command_line(['manage.py', 'createsuperuser'])

    print("数据库重置完成!")


if __name__ == '__main__':
    reset_database()