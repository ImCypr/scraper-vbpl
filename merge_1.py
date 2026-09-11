
import re
import json
from pathlib import Path
from collections import OrderedDict


# ============================================================
# CẤU HÌNH
# ============================================================

INPUT_DIR = Path("PL2")
OUTPUT_DIR = Path("PL_tong")

JSON_OUTPUT = OUTPUT_DIR / "PL_tong.json"
TEXT_OUTPUT = OUTPUT_DIR / "PL_tong.txt"
EMPTY_OUTPUT = OUTPUT_DIR / "nghi_dinh_trong.txt"
DUPLICATE_OUTPUT = OUTPUT_DIR / "trung_lap.txt"


# ============================================================
# CHUẨN HÓA TEXT
# ============================================================

def clean_text(text):

    if text is None:
        return ""

    text = str(text)

    text = text.replace("\r\n", "\n")
    text = text.replace("\r", "\n")

    lines = []
    previous_empty = False

    for line in text.split("\n"):

        line = line.rstrip()
        stripped = line.strip()

        if not stripped:

            if not previous_empty:
                lines.append("")

            previous_empty = True

        else:

            lines.append(stripped)
            previous_empty = False

    return "\n".join(lines).strip()


# ============================================================
# CHUẨN HÓA SỐ HIỆU
# ============================================================

def normalize_doc_number(doc_number):

    if not doc_number:
        return ""

    doc_number = str(doc_number).strip()

    doc_number = re.sub(
        r"\s+",
        "",
        doc_number
    )

    doc_number = doc_number.replace(
        "–",
        "-"
    )

    doc_number = doc_number.replace(
        "—",
        "-"
    )

    return doc_number.upper()


# ============================================================
# LẤY SỐ HIỆU TỪ JSON
# ============================================================

def get_doc_number_from_json(data):

    if not isinstance(data, dict):
        return ""

    return normalize_doc_number(
        data.get(
            "doc_number",
            ""
        )
    )


# ============================================================
# LẤY SỐ HIỆU TỪ TEXT
# ============================================================

def get_doc_number_from_text(text):

    if not text:
        return ""

    # --------------------------------------------------------
    # Số hiệu: 01/2019/TT-BXD
    # --------------------------------------------------------

    match = re.search(
        r"Số\s*hiệu\s*:\s*([^\n\r]+)",
        text,
        re.IGNORECASE
    )

    if match:

        value = match.group(1).strip()

        value = re.split(
            r"\s{2,}|\|",
            value
        )[0].strip()

        return normalize_doc_number(
            value
        )

    # --------------------------------------------------------
    # Tìm trực tiếp số hiệu
    # --------------------------------------------------------

    patterns = [

        r"\b\d{1,5}/\d{4}/[A-ZĐ]+(?:-[A-ZĐ0-9]+)+\b",

        r"\b\d{1,5}/\d{4}/[A-ZĐ]+-[A-ZĐ0-9]+\b"

    ]

    for pattern in patterns:

        match = re.search(
            pattern,
            text,
            re.IGNORECASE
        )

        if match:

            return normalize_doc_number(
                match.group(0)
            )

    return ""


# ============================================================
# KIỂM TRA ĐIỀU
# ============================================================

def is_article(node):

    if not isinstance(node, dict):
        return False

    level = str(
        node.get("level", "")
    ).lower().strip()

    number = str(
        node.get("number", "")
    ).strip()

    if level == "dieu":
        return True

    if re.match(
        r"^Điều\s+\d+",
        number,
        re.IGNORECASE
    ):
        return True

    return False


# ============================================================
# KIỂM TRA KHOẢN
# ============================================================

def is_clause(node):

    if not isinstance(node, dict):
        return False

    level = str(
        node.get("level", "")
    ).lower().strip()

    number = str(
        node.get("number", "")
    ).strip()

    if level == "khoan":
        return True

    if re.match(
        r"^Khoản\s+\d+",
        number,
        re.IGNORECASE
    ):
        return True

    return False


# ============================================================
# KIỂM TRA ĐIỂM
# ============================================================

def is_point(node):

    if not isinstance(node, dict):
        return False

    level = str(
        node.get("level", "")
    ).lower().strip()

    number = str(
        node.get("number", "")
    ).strip()

    if level in {
        "diem",
        "point"
    }:
        return True

    if re.match(
        r"^[a-zđ]\s*[\)\.]?$",
        number,
        re.IGNORECASE
    ):
        return True

    if re.match(
        r"^[a-zđ]\s*[\)\.]",
        number,
        re.IGNORECASE
    ):
        return True

    return False


# ============================================================
# LẤY SỐ ĐIỀU
# ============================================================

def normalize_article_number(number):

    number = clean_text(number)

    if not number:
        return ""

    match = re.search(
        r"Điều\s+(\d+[A-Za-z]?)",
        number,
        re.IGNORECASE
    )

    if match:
        return f"Điều {match.group(1)}"

    return number


# ============================================================
# LẤY SỐ KHOẢN
# ============================================================

def get_clause_number(number):

    number = clean_text(number)

    match = re.search(
        r"Khoản\s+(\d+)",
        number,
        re.IGNORECASE
    )

    if match:
        return match.group(1)

    match = re.match(
        r"^\s*(\d+)\s*$",
        number
    )

    if match:
        return match.group(1)

    return number


# ============================================================
# LẤY KÝ HIỆU ĐIỂM
# ============================================================

def get_point_number(number):

    number = clean_text(number)

    match = re.match(
        r"^\s*([a-zđ])",
        number,
        re.IGNORECASE
    )

    if match:
        return match.group(1).lower() + ")"

    return number


# ============================================================
# LẤY KÝ HIỆU NODE
# ============================================================

def get_node_number(node):

    number = clean_text(
        node.get(
            "number",
            ""
        )
    )

    if not number:
        return ""

    # --------------------------------------------------------
    # Điều
    # --------------------------------------------------------

    if is_article(node):

        return normalize_article_number(
            number
        )

    # --------------------------------------------------------
    # Khoản
    # --------------------------------------------------------

    if is_clause(node):

        return get_clause_number(
            number
        ) + "."

    # --------------------------------------------------------
    # Điểm
    # --------------------------------------------------------

    if is_point(node):

        return get_point_number(
            number
        )

    # --------------------------------------------------------
    # Node khác
    # --------------------------------------------------------

    return number


# ============================================================
# XÓA KÝ HIỆU TRÙNG Ở ĐẦU CONTENT
# ============================================================

def remove_leading_number(
    text,
    node
):

    if not text:
        return ""

    text = text.strip()

    number = clean_text(
        node.get(
            "number",
            ""
        )
    )

    if not number:
        return text

    # ========================================================
    # KHOẢN
    # ========================================================

    if is_clause(node):

        clause_number = get_clause_number(
            number
        )

        text = re.sub(
            rf"^\s*"
            rf"{re.escape(clause_number)}"
            rf"\s*[\.\)]\s*",
            "",
            text
        )

        return text.strip()

    # ========================================================
    # ĐIỂM
    # ========================================================

    if is_point(node):

        point_number = get_point_number(
            number
        )

        if point_number:

            letter = point_number[0]

            text = re.sub(
                rf"^\s*"
                rf"{re.escape(letter)}"
                rf"\s*[\.\)]\s*",
                "",
                text,
                flags=re.IGNORECASE
            )

        return text.strip()

    return text


# ============================================================
# RENDER NODE THEO CẤP
# ============================================================

def render_node(
    node,
    level=0
):

    if not isinstance(
        node,
        dict
    ):
        return []

    lines = []

    node_level = str(
        node.get(
            "level",
            ""
        )
    ).lower().strip()

    number = clean_text(
        node.get(
            "number",
            ""
        )
    )

    title = clean_text(
        node.get(
            "title",
            ""
        )
    )

    content = clean_text(
        node.get(
            "content",
            ""
        )
    )

    children = node.get(
        "children",
        []
    )

    if not isinstance(
        children,
        list
    ):
        children = []

    # ========================================================
    # NỘI DUNG
    # ========================================================

    text = content or title

    # Loại số thứ tự đã nằm trong content
    text = remove_leading_number(
        text,
        node
    )

    # ========================================================
    # ĐIỀU
    # ========================================================

    if is_article(node):

        article_number = normalize_article_number(
            number
        )

        if text:

            lines.append(
                f"{article_number}. {text}"
            )

        else:

            lines.append(
                article_number
            )

        # Điều luôn bắt đầu ở cấp 0
        child_level = 1

    # ========================================================
    # KHOẢN
    # ========================================================

    elif is_clause(node):

        clause_number = get_clause_number(
            number
        )

        indent = "    " * level

        if text:

            lines.append(
                f"{indent}{clause_number}. {text}"
            )

        else:

            lines.append(
                f"{indent}{clause_number}."
            )

        child_level = level + 1

    # ========================================================
    # ĐIỂM
    # ========================================================

    elif is_point(node):

        point_number = get_point_number(
            number
        )

        indent = "    " * level

        if text:

            lines.append(
                f"{indent}{point_number} {text}"
            )

        else:

            lines.append(
                f"{indent}{point_number}"
            )

        child_level = level + 1

    # ========================================================
    # NODE KHÁC
    # ========================================================

    else:

        indent = "    " * level

        if text:

            lines.append(
                f"{indent}{text}"
            )

        child_level = level + 1

    # ========================================================
    # NODE CON
    # ========================================================

    for child in children:

        child_lines = render_node(
            child,
            child_level
        )

        if child_lines:

            lines.extend(
                child_lines
            )

    return lines


# ============================================================
# KIỂM TRA JSON CÓ ĐIỀU/KHOẢN
# ============================================================

def json_has_legal_content(data):

    if not isinstance(
        data,
        dict
    ):
        return False

    content_tree = data.get(
        "content_tree"
    )

    if not isinstance(
        content_tree,
        list
    ):
        return False

    if not content_tree:
        return False

    def recursive_check(nodes):

        for node in nodes:

            if not isinstance(
                node,
                dict
            ):
                continue

            if (
                is_article(node)
                or is_clause(node)
            ):
                return True

            children = node.get(
                "children",
                []
            )

            if isinstance(
                children,
                list
            ):

                if recursive_check(
                    children
                ):
                    return True

        return False

    return recursive_check(
        content_tree
    )


# ============================================================
# JSON → TEXT
# ============================================================

def json_to_text(data):

    title = clean_text(
        data.get(
            "title",
            ""
        )
    )

    doc_number = clean_text(
        data.get(
            "doc_number",
            ""
        )
    )

    issued_date = clean_text(
        data.get(
            "issued_date",
            ""
        )
    )

    status = clean_text(
        data.get(
            "status",
            ""
        )
    )

    source_url = clean_text(
        data.get(
            "source_url",
            ""
        )
    )

    lines = []

    # ========================================================
    # TÊN VĂN BẢN
    # ========================================================

    if title:

        lines.append(
            title
        )

    # ========================================================
    # SỐ HIỆU
    # ========================================================

    if doc_number:

        lines.append(
            f"Số hiệu: {doc_number}"
        )

    # ========================================================
    # NGÀY + TRẠNG THÁI
    # ========================================================

    date_line = "Ngày:"

    if issued_date:

        date_line += f" {issued_date}"

    if status:

        date_line += (
            f"  |  Trạng thái: {status}"
        )

    lines.append(
        date_line
    )

    # ========================================================
    # SOURCE
    # ========================================================

    if source_url:

        lines.append(
            f"Nguồn: {source_url}"
        )

    lines.append(
        "-" * 60
    )

    lines.append("")

    # ========================================================
    # CONTENT TREE
    # ========================================================

    content_tree = data.get(
        "content_tree",
        []
    )

    if isinstance(
        content_tree,
        list
    ):

        for node in content_tree:

            node_lines = render_node(
                node,
                level=0
            )

            if node_lines:

                lines.extend(
                    node_lines
                )

                lines.append("")

    return clean_text(
        "\n".join(lines)
    )


# ============================================================
# KIỂM TRA TXT CÓ NỘI DUNG
# ============================================================

def text_has_legal_content(text):

    if not text:
        return False

    # Điều
    if re.search(
        r"(?m)^\s*Điều\s+\d+",
        text,
        re.IGNORECASE
    ):
        return True

    # Khoản
    if re.search(
        r"(?m)^\s*Khoản\s+\d+",
        text,
        re.IGNORECASE
    ):
        return True

    # 1. Nội dung
    if re.search(
        r"(?m)^\s*\d+\.\s+\S+",
        text
    ):
        return True

    return False


# ============================================================
# CHUẨN HÓA TEXT
# ============================================================

def normalize_text_file(text):

    if not text:
        return ""

    text = clean_text(
        text
    )

    if not text:
        return ""

    # ========================================================
    # Đường phân cách
    # ========================================================

    text = re.sub(
        r"(?m)^[=\-─━]{5,}\s*$",
        "-" * 60,
        text
    )

    lines = []

    for line in text.split("\n"):

        stripped = line.strip()

        # ====================================================
        # ĐIỀU
        # ====================================================

        match = re.match(
            r"^Điều\s+(\d+)"
            r"\s*[–—\-:]\s*(.*)$",
            stripped,
            re.IGNORECASE
        )

        if match:

            number = match.group(1)
            content = match.group(2).strip()

            lines.append(
                f"Điều {number}. {content}"
            )

            continue

        # ====================================================
        # ĐIỀU CHỈ CÓ SỐ
        # ====================================================

        match = re.match(
            r"^Điều\s+(\d+)\s*$",
            stripped,
            re.IGNORECASE
        )

        if match:

            lines.append(
                f"Điều {match.group(1)}."
            )

            continue

        # ====================================================
        # KHOẢN ĐỨNG RIÊNG
        # ====================================================

        match = re.match(
            r"^Khoản\s+(\d+)\s*[.:]?\s*$",
            stripped,
            re.IGNORECASE
        )

        if match:

            number = match.group(1)

            lines.append(
                f"    {number}."
            )

            continue

        # ====================================================
        # ĐIỂM
        # ====================================================

        match = re.match(
            r"^([a-zđ])\s*[\)\.]\s*(.*)$",
            stripped,
            re.IGNORECASE
        )

        if match:

            letter = match.group(1).lower()
            content = match.group(2).strip()

            if content:

                lines.append(
                    f"        {letter}) {content}"
                )

            else:

                lines.append(
                    f"        {letter})"
                )

            continue

        # ====================================================
        # DÒNG THƯỜNG
        # ====================================================

        lines.append(
            stripped
        )

    return clean_text(
        "\n".join(lines)
    )


# ============================================================
# ĐỌC JSON
# ============================================================

def load_json_file(path):

    try:

        with open(
            path,
            "r",
            encoding="utf-8-sig"
        ) as f:

            return json.load(f)

    except json.JSONDecodeError as e:

        print(
            f"[LỖI JSON] {path.name}: {e}"
        )

        return None

    except Exception as e:

        print(
            f"[LỖI] {path.name}: {e}"
        )

        return None


# ============================================================
# ĐỌC TEXT
# ============================================================

def load_text_file(path):

    encodings = [
        "utf-8-sig",
        "utf-8",
        "cp1258"
    ]

    for encoding in encodings:

        try:

            with open(
                path,
                "r",
                encoding=encoding
            ) as f:

                return f.read()

        except UnicodeDecodeError:

            continue

        except Exception as e:

            print(
                f"[LỖI TXT] {path.name}: {e}"
            )

            return ""

    print(
        f"[LỖI ENCODING] {path.name}"
    )

    return ""


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 70)
    print("CÔNG CỤ GỘP DỮ LIỆU PHÁP LUẬT")
    print("THỤT ĐẦU DÒNG THEO CẤP + CHECK TRÙNG")
    print("=" * 70)

    # ========================================================
    # KIỂM TRA THƯ MỤC
    # ========================================================

    if not INPUT_DIR.exists():

        print(
            f"[LỖI] Không tìm thấy thư mục "
            f"{INPUT_DIR}"
        )

        input(
            "\nNhấn Enter để thoát..."
        )

        return

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    # ========================================================
    # XÓA KẾT QUẢ CŨ
    # ========================================================

    for output_file in [
        JSON_OUTPUT,
        TEXT_OUTPUT,
        EMPTY_OUTPUT,
        DUPLICATE_OUTPUT
    ]:

        if output_file.exists():

            try:

                output_file.unlink()

            except Exception as e:

                print(
                    f"[CẢNH BÁO] Không thể xóa "
                    f"{output_file}: {e}"
                )

    # ========================================================
    # DỮ LIỆU
    # ========================================================

    json_documents = []

    text_documents = []

    empty_files = []

    # ========================================================
    # THEO DÕI VĂN BẢN TRÙNG
    # ========================================================

    seen_doc_numbers = set()

    duplicate_tracker = OrderedDict()

    json_count = 0
    text_count = 0
    duplicate_count = 0

    # ========================================================
    # XỬ LÝ JSON
    # ========================================================

    json_files = sorted(
        INPUT_DIR.glob("*.json")
    )

    print(
        f"\nTìm thấy "
        f"{len(json_files)} file JSON."
    )

    for index, path in enumerate(
        json_files,
        start=1
    ):

        print(
            f"\n[JSON {index}/{len(json_files)}] "
            f"{path.name}"
        )

        data = load_json_file(
            path
        )

        if data is None:

            continue

        # ----------------------------------------------------
        # Kiểm tra nội dung
        # ----------------------------------------------------

        if not json_has_legal_content(
            data
        ):

            empty_files.append(
                path.name
            )

            print(
                "    -> BỎ QUA: "
                "không có Điều/Khoản"
            )

            continue

        # ----------------------------------------------------
        # Lấy số hiệu
        # ----------------------------------------------------

        doc_number = get_doc_number_from_json(
            data
        )

        # ====================================================
        # CHECK TRÙNG
        # ====================================================

        if doc_number:

            if doc_number in seen_doc_numbers:

                duplicate_count += 1

                if doc_number not in duplicate_tracker:

                    duplicate_tracker[
                        doc_number
                    ] = {
                        "count": 1,
                        "files": []
                    }

                duplicate_tracker[
                    doc_number
                ]["count"] += 1

                duplicate_tracker[
                    doc_number
                ]["files"].append(
                    path.name
                )

                print(
                    f"    -> TRÙNG: "
                    f"{doc_number}"
                )

                print(
                    "    -> Không ghép"
                )

                continue

            # Văn bản đầu tiên
            seen_doc_numbers.add(
                doc_number
            )

            duplicate_tracker[
                doc_number
            ] = {
                "count": 1,
                "files": [
                    path.name
                ]
            }

        # ====================================================
        # THÊM JSON
        # ====================================================

        json_documents.append(
            data
        )

        # ====================================================
        # JSON → TXT
        # ====================================================

        formatted_text = json_to_text(
            data
        )

        if formatted_text:

            text_documents.append(
                formatted_text
            )

        json_count += 1

        print(
            "    -> GHÉP VÀO TỔNG"
        )

    # ========================================================
    # XỬ LÝ TXT
    # ========================================================

    text_files = sorted(
        INPUT_DIR.glob("*.txt")
    )

    print(
        f"\nTìm thấy "
        f"{len(text_files)} file TXT."
    )

    for index, path in enumerate(
        text_files,
        start=1
    ):

        print(
            f"\n[TXT {index}/{len(text_files)}] "
            f"{path.name}"
        )

        raw_text = load_text_file(
            path
        )

        if not raw_text.strip():

            empty_files.append(
                path.name
            )

            print(
                "    -> BỎ QUA: file rỗng"
            )

            continue

        # ----------------------------------------------------
        # Kiểm tra nội dung
        # ----------------------------------------------------

        if not text_has_legal_content(
            raw_text
        ):

            empty_files.append(
                path.name
            )

            print(
                "    -> BỎ QUA: "
                "không có Điều/Khoản"
            )

            continue

        # ----------------------------------------------------
        # Lấy số hiệu
        # ----------------------------------------------------

        doc_number = get_doc_number_from_text(
            raw_text
        )

        # ====================================================
        # CHECK TRÙNG
        # ====================================================

        if doc_number:

            if doc_number in seen_doc_numbers:

                duplicate_count += 1

                if doc_number not in duplicate_tracker:

                    duplicate_tracker[
                        doc_number
                    ] = {
                        "count": 1,
                        "files": []
                    }

                duplicate_tracker[
                    doc_number
                ]["count"] += 1

                duplicate_tracker[
                    doc_number
                ]["files"].append(
                    path.name
                )

                print(
                    f"    -> TRÙNG: "
                    f"{doc_number}"
                )

                print(
                    "    -> Không ghép"
                )

                continue

            seen_doc_numbers.add(
                doc_number
            )

            duplicate_tracker[
                doc_number
            ] = {
                "count": 1,
                "files": [
                    path.name
                ]
            }

        # ====================================================
        # CHUẨN HÓA TXT
        # ====================================================

        formatted_text = normalize_text_file(
            raw_text
        )

        if formatted_text:

            text_documents.append(
                formatted_text
            )

            text_count += 1

            print(
                "    -> GHÉP VÀO TỔNG"
            )

        else:

            empty_files.append(
                path.name
            )

            print(
                "    -> BỎ QUA"
            )

    # ========================================================
    # GHI JSON TỔNG
    # ========================================================

    print(
        "\nĐang tạo PL_tong.json..."
    )

    with open(
        JSON_OUTPUT,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            json_documents,
            f,
            ensure_ascii=False,
            indent=2
        )

    # ========================================================
    # GHI TEXT TỔNG
    # ========================================================

    print(
        "Đang tạo PL_tong.txt..."
    )

    with open(
        TEXT_OUTPUT,
        "w",
        encoding="utf-8"
    ) as f:

        for index, document in enumerate(
            text_documents
        ):

            f.write(
                document.strip()
            )

            f.write(
                "\n"
            )

            if index < len(
                text_documents
            ) - 1:

                f.write(
                    "\n"
                    + "=" * 70
                    + "\n\n"
                )

    # ========================================================
    # GHI FILE KHÔNG CÓ ĐIỀU/KHOẢN
    # ========================================================

    print(
        "Đang tạo "
        "nghi_dinh_trong.txt..."
    )

    with open(
        EMPTY_OUTPUT,
        "w",
        encoding="utf-8"
    ) as f:

        if empty_files:

            f.write(
                "DANH SÁCH FILE KHÔNG CÓ "
                "ĐIỀU/KHOẢN\n"
            )

            f.write(
                "=" * 60
                + "\n\n"
            )

            for index, filename in enumerate(
                empty_files,
                start=1
            ):

                f.write(
                    f"{index}. {filename}\n"
                )

        else:

            f.write(
                "Không có file nào "
                "bị bỏ qua.\n"
            )

    # ========================================================
    # GHI FILE TRÙNG
    # ========================================================

    print(
        "Đang tạo trung_lap.txt..."
    )

    with open(
        DUPLICATE_OUTPUT,
        "w",
        encoding="utf-8"
    ) as f:

        duplicated_documents = [

            (
                doc_number,
                info
            )

            for doc_number, info
            in duplicate_tracker.items()

            if info["count"] > 1
        ]

        if duplicated_documents:

            f.write(
                "DANH SÁCH VĂN BẢN TRÙNG\n"
            )

            f.write(
                "=" * 70
                + "\n\n"
            )

            for index, (
                doc_number,
                info
            ) in enumerate(
                duplicated_documents,
                start=1
            ):

                f.write(
                    f"{index}. {doc_number}\n"
                )

                f.write(
                    f"   Số lần xuất hiện: "
                    f"{info['count']}\n"
                )

                f.write(
                    "   File:\n"
                )

                for filename in info["files"]:

                    f.write(
                        f"      - {filename}\n"
                    )

                f.write(
                    "\n"
                )

        else:

            f.write(
                "Không phát hiện văn bản trùng.\n"
            )

    # ========================================================
    # THỐNG KÊ
    # ========================================================

    unique_documents = len(
        seen_doc_numbers
    )

    duplicated_document_types = sum(
        1
        for info in duplicate_tracker.values()
        if info["count"] > 1
    )

    print(
        "\n"
        + "=" * 70
    )

    print(
        "HOÀN THÀNH"
    )

    print(
        "=" * 70
    )

    print(
        f"JSON được ghép       : {json_count}"
    )

    print(
        f"TXT được ghép        : {text_count}"
    )

    print(
        f"File không có nội dung: "
        f"{len(empty_files)}"
    )

    print(
        f"Văn bản duy nhất     : "
        f"{unique_documents}"
    )

    print(
        f"Lượt phát hiện trùng : "
        f"{duplicate_count}"
    )

    print(
        f"Loại văn bản bị trùng: "
        f"{duplicated_document_types}"
    )

    print(
        "\nKết quả:"
    )

    print(
        f"  JSON: {JSON_OUTPUT}"
    )

    print(
        f"  TXT : {TEXT_OUTPUT}"
    )

    print(
        f"  File trống: {EMPTY_OUTPUT}"
    )

    print(
        f"  File trùng: {DUPLICATE_OUTPUT}"
    )

    print(
        "=" * 70
    )

    input(
        "\nNhấn Enter để thoát..."
    )


# ============================================================
# CHẠY
# ============================================================

if __name__ == "__main__":
    main()

