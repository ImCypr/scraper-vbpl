import ast
import os
import sys
import subprocess
from pathlib import Path


# ============================================================
# CẤU HÌNH
# ============================================================

# Thư mục dự án cần quét
PROJECT_DIR = Path(".").resolve()

# File output
OUTPUT_FILE = PROJECT_DIR / "requirements.txt"

# Các thư mục không cần quét
EXCLUDE_DIRS = {
    ".git",
    ".venv",
    "venv",
    "env",
    "__pycache__",
    "node_modules",
    ".idea",
    ".vscode",
}


# ============================================================
# LẤY IMPORT TỪ FILE PYTHON
# ============================================================

def get_imports_from_file(file_path):
    imports = set()

    try:
        source = file_path.read_text(
            encoding="utf-8",
            errors="ignore"
        )

        tree = ast.parse(source, filename=str(file_path))

        for node in ast.walk(tree):

            # import numpy
            # import pandas as pd
            if isinstance(node, ast.Import):
                for alias in node.names:
                    name = alias.name.split(".")[0]
                    imports.add(name)

            # from bs4 import BeautifulSoup
            # from sklearn.model_selection import ...
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    name = node.module.split(".")[0]
                    imports.add(name)

    except Exception as e:
        print(f"[WARNING] Không đọc được: {file_path}")
        print(f"         {e}")

    return imports


# ============================================================
# QUÉT TOÀN BỘ PROJECT
# ============================================================

def scan_project(project_dir):

    imports = set()

    print("=" * 60)
    print("ĐANG QUÉT PROJECT")
    print("=" * 60)

    for root, dirs, files in os.walk(project_dir):

        # Loại bỏ thư mục không cần quét
        dirs[:] = [
            d for d in dirs
            if d not in EXCLUDE_DIRS
        ]

        for file in files:

            if not file.endswith(".py"):
                continue

            file_path = Path(root) / file

            print(f"[SCAN] {file_path}")

            file_imports = get_imports_from_file(file_path)

            imports.update(file_imports)

    return imports


# ============================================================
# LẤY DANH SÁCH PACKAGE ĐÃ CÀI
# ============================================================

def get_installed_packages():

    print("\n" + "=" * 60)
    print("ĐANG KIỂM TRA PACKAGE ĐÃ CÀI")
    print("=" * 60)

    try:

        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "pip",
                "list",
                "--format=json"
            ],
            capture_output=True,
            text=True,
            check=True
        )

        import json

        data = json.loads(result.stdout)

        packages = {}

        for package in data:
            name = package["name"]
            version = package["version"]

            packages[name.lower()] = (
                name,
                version
            )

        return packages

    except Exception as e:

        print("[ERROR] Không lấy được danh sách package.")
        print(e)

        return {}


# ============================================================
# MAP IMPORT → PACKAGE
# ============================================================

# Một số package có tên import khác tên pip package
IMPORT_TO_PACKAGE = {

    "bs4": "beautifulsoup4",
    "cv2": "opencv-python",
    "sklearn": "scikit-learn",
    "yaml": "PyYAML",
    "PIL": "Pillow",
    "dotenv": "python-dotenv",
    "fitz": "PyMuPDF",
    "Crypto": "pycryptodome",
    "dateutil": "python-dateutil",
    "google": "google",
}


# ============================================================
# TẠO REQUIREMENTS.TXT
# ============================================================

def create_requirements(imports, installed_packages):

    requirements = []

    standard_library = {
        "os",
        "sys",
        "json",
        "re",
        "time",
        "math",
        "random",
        "datetime",
        "pathlib",
        "typing",
        "collections",
        "itertools",
        "functools",
        "subprocess",
        "threading",
        "asyncio",
        "logging",
        "traceback",
        "shutil",
        "glob",
        "pickle",
        "sqlite3",
        "statistics",
        "string",
        "csv",
        "hashlib",
        "base64",
        "urllib",
        "http",
        "email",
        "socket",
        "queue",
        "dataclasses",
        "enum",
        "abc",
        "contextlib",
        "inspect",
        "platform",
        "tempfile",
        "warnings",
        "unittest",
    }

    print("\n" + "=" * 60)
    print("ĐỐI CHIẾU IMPORT → PACKAGE")
    print("=" * 60)

    for import_name in sorted(imports):

        if import_name.lower() in {
            x.lower() for x in standard_library
        }:
            continue

        package_name = IMPORT_TO_PACKAGE.get(
            import_name,
            import_name
        )

        package_info = installed_packages.get(
            package_name.lower()
        )

        if package_info:

            real_name, version = package_info

            requirements.append(
                f"{real_name}=={version}"
            )

            print(
                f"[OK] {import_name:<20} "
                f"-> {real_name}=={version}"
            )

        else:

            print(
                f"[??] {import_name:<20} "
                f"-> Không tìm thấy package"
            )

    return sorted(set(requirements), key=str.lower)


# ============================================================
# MAIN
# ============================================================

def main():

    print("\n")
    print("=" * 60)
    print(" PYTHON REQUIREMENTS GENERATOR")
    print("=" * 60)

    print(f"\nProject: {PROJECT_DIR}")
    print(f"Python : {sys.executable}")

    # 1. Quét import
    imports = scan_project(PROJECT_DIR)

    print(
        f"\nTìm thấy {len(imports)} module/package được import."
    )

    # 2. Lấy package đã cài
    installed_packages = get_installed_packages()

    # 3. Đối chiếu
    requirements = create_requirements(
        imports,
        installed_packages
    )

    # 4. Ghi file
    with open(
        OUTPUT_FILE,
        "w",
        encoding="utf-8"
    ) as f:

        for package in requirements:
            f.write(package + "\n")

    print("\n" + "=" * 60)
    print("HOÀN TẤT")
    print("=" * 60)

    print(f"\nĐã tạo:")
    print(f"  {OUTPUT_FILE}")

    print(f"\nTổng số package: {len(requirements)}")

    print("\nDanh sách:")

    for package in requirements:
        print(f"  {package}")


if __name__ == "__main__":
    main()