import filecmp
import os
from typing import Dict, List


def compare_folders(left: str, right: str) -> Dict[str, List[str]]:
    """
    对比两个文件夹，返回新增、删除、修改的文件列表。

    Args:
        left: 原始文件夹路径（基准）
        right: 目标文件夹路径（对比）

    Returns:
        包含三个键的字典：
        - 'added': 新增文件列表（只在 right 中存在）
        - 'deleted': 删除文件列表（只在 left 中存在）
        - 'modified': 修改文件列表（两边都存在但内容不同）
    """
    result = {
        'added': [],
        'deleted': [],
        'modified': []
    }

    def _compare_dirs(left_dir: str, right_dir: str, base_path: str = ''):
        left_abs = os.path.join(left, left_dir) if left_dir else left
        right_abs = os.path.join(right, right_dir) if right_dir else right

        dcmp = filecmp.dircmp(left_abs, right_abs)

        for name in dcmp.left_only:
            full_path = os.path.join(base_path, name)
            abs_path = os.path.join(left_abs, name)
            if os.path.isdir(abs_path):
                _collect_files(abs_path, full_path, result['deleted'])
            else:
                result['deleted'].append(full_path)

        for name in dcmp.right_only:
            full_path = os.path.join(base_path, name)
            abs_path = os.path.join(right_abs, name)
            if os.path.isdir(abs_path):
                _collect_files(abs_path, full_path, result['added'])
            else:
                result['added'].append(full_path)

        for name in dcmp.diff_files:
            full_path = os.path.join(base_path, name)
            result['modified'].append(full_path)

        for name in dcmp.common_dirs:
            sub_left = os.path.join(left_dir, name) if left_dir else name
            sub_right = os.path.join(right_dir, name) if right_dir else name
            sub_base = os.path.join(base_path, name)
            _compare_dirs(sub_left, sub_right, sub_base)

    def _collect_files(root: str, base_path: str, collector: List[str]):
        for dirpath, dirnames, filenames in os.walk(root):
            rel_dir = os.path.relpath(dirpath, root)
            for filename in filenames:
                if rel_dir == '.':
                    file_path = os.path.join(base_path, filename)
                else:
                    file_path = os.path.join(base_path, rel_dir, filename)
                collector.append(file_path)

    if not os.path.exists(left):
        raise FileNotFoundError(f"文件夹不存在: {left}")
    if not os.path.exists(right):
        raise FileNotFoundError(f"文件夹不存在: {right}")

    _compare_dirs('', '')

    for key in result:
        result[key].sort()

    return result


def format_result(result: Dict[str, List[str]]) -> str:
    """
    格式化对比结果为易读的字符串。
    """
    lines = []
    lines.append('=' * 60)
    lines.append('文件夹对比结果')
    lines.append('=' * 60)

    for status, files in result.items():
        status_cn = {
            'added': '新增',
            'deleted': '删除',
            'modified': '修改'
        }[status]
        lines.append(f'\n【{status_cn}】共 {len(files)} 个文件:')
        if files:
            for f in files:
                lines.append(f'  - {f}')
        else:
            lines.append('  (无)')

    lines.append('\n' + '=' * 60)
    total = sum(len(v) for v in result.values())
    lines.append(f'总计: {total} 个文件发生变化')
    lines.append('=' * 60)

    return '\n'.join(lines)


if __name__ == '__main__':
    import sys

    if len(sys.argv) != 3:
        print('用法: python folder_diff.py <原始文件夹> <目标文件夹>')
        print('示例: python folder_diff.py ./v1 ./v2')
        sys.exit(1)

    left_folder = sys.argv[1]
    right_folder = sys.argv[2]

    try:
        diff_result = compare_folders(left_folder, right_folder)
        print(format_result(diff_result))
    except FileNotFoundError as e:
        print(f'错误: {e}')
        sys.exit(1)
