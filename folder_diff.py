import filecmp
import os
import shutil
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


def sync_folders(source: str, target: str, delete_extra: bool = False, dry_run: bool = False) -> Dict[str, List[str]]:
    """
    同步源文件夹到目标文件夹，将差异文件复制到目标文件夹。

    Args:
        source: 源文件夹路径（基准）
        target: 目标文件夹路径
        delete_extra: 是否删除目标中多余的文件（即源中不存在的文件）
        dry_run: 试运行模式，只显示将要执行的操作，不实际执行

    Returns:
        包含同步操作详情的字典：
        - 'copied': 复制的文件列表（新增+修改）
        - 'deleted': 删除的文件列表（仅 delete_extra=True 时有值）
        - 'skipped': 跳过的文件列表
    """
    sync_result = {
        'copied': [],
        'deleted': [],
        'skipped': []
    }

    diff = compare_folders(source, target)

    for file_path in diff['deleted']:
        src_abs = os.path.join(source, file_path)
        dst_abs = os.path.join(target, file_path)
        if not dry_run:
            os.makedirs(os.path.dirname(dst_abs), exist_ok=True)
            shutil.copy2(src_abs, dst_abs)
        sync_result['copied'].append(file_path)

    for file_path in diff['modified']:
        src_abs = os.path.join(source, file_path)
        dst_abs = os.path.join(target, file_path)
        if not dry_run:
            os.makedirs(os.path.dirname(dst_abs), exist_ok=True)
            shutil.copy2(src_abs, dst_abs)
        sync_result['copied'].append(file_path)

    if delete_extra:
        for file_path in diff['added']:
            dst_abs = os.path.join(target, file_path)
            if not dry_run:
                if os.path.isfile(dst_abs):
                    os.remove(dst_abs)
            sync_result['deleted'].append(file_path)

        _clean_empty_dirs(target)
    else:
        sync_result['skipped'] = diff['added']

    return sync_result


def _clean_empty_dirs(root: str):
    """
    递归清理空目录。
    """
    if not os.path.isdir(root):
        return

    for name in os.listdir(root):
        path = os.path.join(root, name)
        if os.path.isdir(path):
            _clean_empty_dirs(path)

    try:
        os.rmdir(root)
    except OSError:
        pass


def format_sync_result(result: Dict[str, List[str]], dry_run: bool = False) -> str:
    """
    格式化同步结果为易读的字符串。
    """
    prefix = '[试运行] ' if dry_run else ''
    lines = []
    lines.append('=' * 60)
    lines.append(f'{prefix}文件夹同步结果')
    lines.append('=' * 60)

    lines.append(f'\n【复制】共 {len(result["copied"])} 个文件:')
    if result['copied']:
        for f in result['copied']:
            lines.append(f'  + {f}')
    else:
        lines.append('  (无)')

    if result['deleted']:
        lines.append(f'\n【删除】共 {len(result["deleted"])} 个文件:')
        for f in result['deleted']:
            lines.append(f'  - {f}')

    if result['skipped']:
        lines.append(f'\n【跳过】共 {len(result["skipped"])} 个文件（目标中多余的）:')
        for f in result['skipped']:
            lines.append(f'  ~ {f}')

    lines.append('\n' + '=' * 60)
    total = len(result['copied']) + len(result['deleted'])
    lines.append(f'总计: {total} 个文件变更')
    lines.append('=' * 60)

    return '\n'.join(lines)


if __name__ == '__main__':
    import sys
    import argparse

    parser = argparse.ArgumentParser(description='文件夹对比与同步工具')
    parser.add_argument('source', help='源文件夹路径')
    parser.add_argument('target', help='目标文件夹路径')
    parser.add_argument('--sync', action='store_true', help='执行同步操作')
    parser.add_argument('--delete', action='store_true', help='同步时删除目标中多余的文件')
    parser.add_argument('--dry-run', action='store_true', help='试运行模式，不实际执行')

    args = parser.parse_args()

    try:
        if args.sync:
            sync_result = sync_folders(
                args.source,
                args.target,
                delete_extra=args.delete,
                dry_run=args.dry_run
            )
            print(format_sync_result(sync_result, dry_run=args.dry_run))
        else:
            diff_result = compare_folders(args.source, args.target)
            print(format_result(diff_result))
    except FileNotFoundError as e:
        print(f'错误: {e}')
        sys.exit(1)
