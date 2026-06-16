import os
import shutil
import tempfile
from folder_diff import compare_folders, format_result, sync_folders, format_sync_result


def create_test_file(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)


def test_compare():
    print("=" * 60)
    print("测试1: 文件夹对比功能")
    print("=" * 60)

    base_dir = tempfile.mkdtemp(prefix='diff_test_')
    left = os.path.join(base_dir, 'v1')
    right = os.path.join(base_dir, 'v2')

    create_test_file(os.path.join(left, 'common.txt'), '相同内容')
    create_test_file(os.path.join(left, 'modified.txt'), '原始内容')
    create_test_file(os.path.join(left, 'deleted.txt'), '要删除的文件')
    create_test_file(os.path.join(left, 'subdir', 'file1.txt'), '子目录文件1')
    create_test_file(os.path.join(left, 'subdir', 'file2.txt'), '子目录文件2')
    create_test_file(os.path.join(left, 'only_in_left', 'deep', 'nested.txt'), '左侧深层文件')

    create_test_file(os.path.join(right, 'common.txt'), '相同内容')
    create_test_file(os.path.join(right, 'modified.txt'), '修改后的内容')
    create_test_file(os.path.join(right, 'added.txt'), '新增文件')
    create_test_file(os.path.join(right, 'subdir', 'file1.txt'), '子目录文件1')
    create_test_file(os.path.join(right, 'subdir', 'file3.txt'), '子目录新增文件')
    create_test_file(os.path.join(right, 'only_in_right', 'deep', 'nested.txt'), '右侧深层文件')

    result = compare_folders(left, right)
    print(format_result(result))
    print()

    def p(*parts):
        return os.path.join(*parts)

    assert p('added.txt') in result['added']
    assert p('only_in_right', 'deep', 'nested.txt') in result['added']
    assert p('subdir', 'file3.txt') in result['added']
    assert len(result['added']) == 3

    assert p('deleted.txt') in result['deleted']
    assert p('only_in_left', 'deep', 'nested.txt') in result['deleted']
    assert p('subdir', 'file2.txt') in result['deleted']
    assert len(result['deleted']) == 3

    assert p('modified.txt') in result['modified']
    assert len(result['modified']) == 1

    assert p('common.txt') not in result['added']
    assert p('common.txt') not in result['deleted']
    assert p('common.txt') not in result['modified']
    assert p('subdir', 'file1.txt') not in result['added']
    assert p('subdir', 'file1.txt') not in result['deleted']
    assert p('subdir', 'file1.txt') not in result['modified']

    print("✅ 对比测试通过!")
    print()

    shutil.rmtree(base_dir)


def test_sync_dry_run():
    print("=" * 60)
    print("测试2: 同步试运行模式")
    print("=" * 60)

    base_dir = tempfile.mkdtemp(prefix='sync_dry_test_')
    source = os.path.join(base_dir, 'source')
    target = os.path.join(base_dir, 'target')

    create_test_file(os.path.join(source, 'new_file.txt'), '新文件')
    create_test_file(os.path.join(source, 'subdir', 'deep.txt'), '深层新文件')
    create_test_file(os.path.join(source, 'common.txt'), '公共内容')

    create_test_file(os.path.join(target, 'common.txt'), '公共内容')
    create_test_file(os.path.join(target, 'extra.txt'), '多余文件')

    before_target_files = set()
    for root, dirs, files in os.walk(target):
        for f in files:
            rel = os.path.relpath(os.path.join(root, f), target)
            before_target_files.add(rel)

    result = sync_folders(source, target, dry_run=True)
    print(format_sync_result(result, dry_run=True))

    after_target_files = set()
    for root, dirs, files in os.walk(target):
        for f in files:
            rel = os.path.relpath(os.path.join(root, f), target)
            after_target_files.add(rel)

    assert before_target_files == after_target_files, "试运行模式不应修改文件"
    assert len(result['copied']) == 2
    assert len(result['skipped']) == 1

    print("✅ 试运行测试通过!")
    print()

    shutil.rmtree(base_dir)


def test_sync_copy_only():
    print("=" * 60)
    print("测试3: 同步 - 仅复制模式（不删除）")
    print("=" * 60)

    base_dir = tempfile.mkdtemp(prefix='sync_copy_test_')
    source = os.path.join(base_dir, 'source')
    target = os.path.join(base_dir, 'target')

    create_test_file(os.path.join(source, 'new_file.txt'), '新文件内容')
    create_test_file(os.path.join(source, 'subdir', 'deep.txt'), '深层文件内容')
    create_test_file(os.path.join(source, 'modified.txt'), '修改后的内容')
    create_test_file(os.path.join(source, 'common.txt'), '公共内容')

    create_test_file(os.path.join(target, 'common.txt'), '公共内容')
    create_test_file(os.path.join(target, 'modified.txt'), '原始内容')
    create_test_file(os.path.join(target, 'extra.txt'), '多余文件')

    result = sync_folders(source, target, delete_extra=False)
    print(format_sync_result(result))

    assert len(result['copied']) == 3
    assert len(result['skipped']) == 1
    assert len(result['deleted']) == 0

    def read_file(path):
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()

    assert os.path.exists(os.path.join(target, 'new_file.txt'))
    assert read_file(os.path.join(target, 'new_file.txt')) == '新文件内容'

    assert os.path.exists(os.path.join(target, 'subdir', 'deep.txt'))
    assert read_file(os.path.join(target, 'subdir', 'deep.txt')) == '深层文件内容'

    assert read_file(os.path.join(target, 'modified.txt')) == '修改后的内容'

    assert os.path.exists(os.path.join(target, 'extra.txt')), "不删除模式应保留多余文件"

    print("✅ 仅复制模式测试通过!")
    print()

    shutil.rmtree(base_dir)


def test_sync_full():
    print("=" * 60)
    print("测试4: 同步 - 完整模式（复制+删除）")
    print("=" * 60)

    base_dir = tempfile.mkdtemp(prefix='sync_full_test_')
    source = os.path.join(base_dir, 'source')
    target = os.path.join(base_dir, 'target')

    create_test_file(os.path.join(source, 'keep.txt'), '保留的文件')
    create_test_file(os.path.join(source, 'subdir', 'file.txt'), '子目录文件')
    create_test_file(os.path.join(source, 'deep', 'a', 'b', 'c', 'nested.txt'), '深层嵌套')

    create_test_file(os.path.join(target, 'keep.txt'), '保留的文件')
    create_test_file(os.path.join(target, 'to_delete.txt'), '要删除的文件')
    create_test_file(os.path.join(target, 'old_dir', 'old.txt'), '旧目录文件')
    create_test_file(os.path.join(target, 'deep', 'a', 'b', 'c', 'old.txt'), '深层旧文件')

    result = sync_folders(source, target, delete_extra=True)
    print(format_sync_result(result))

    assert len(result['copied']) == 2
    assert len(result['deleted']) == 3

    assert os.path.exists(os.path.join(target, 'keep.txt'))
    assert os.path.exists(os.path.join(target, 'subdir', 'file.txt'))
    assert os.path.exists(os.path.join(target, 'deep', 'a', 'b', 'c', 'nested.txt'))

    assert not os.path.exists(os.path.join(target, 'to_delete.txt'))
    assert not os.path.exists(os.path.join(target, 'old_dir', 'old.txt'))
    assert not os.path.exists(os.path.join(target, 'deep', 'a', 'b', 'c', 'old.txt'))
    assert not os.path.exists(os.path.join(target, 'old_dir')), "空目录应被清理"

    diff_after = compare_folders(source, target)
    assert len(diff_after['added']) == 0
    assert len(diff_after['deleted']) == 0
    assert len(diff_after['modified']) == 0

    print("✅ 完整同步测试通过!")
    print()

    shutil.rmtree(base_dir)


def test_sync_deep_nested():
    print("=" * 60)
    print("测试5: 深层嵌套目录同步")
    print("=" * 60)

    base_dir = tempfile.mkdtemp(prefix='sync_deep_test_')
    source = os.path.join(base_dir, 'source')
    target = os.path.join(base_dir, 'target')

    os.makedirs(target)

    for i in range(1, 11):
        path = os.path.join(source, *[f'level{j}' for j in range(1, i + 1)], 'file.txt')
        create_test_file(path, f'source level {i}')

    result = sync_folders(source, target)
    print(f"复制了 {len(result['copied'])} 个文件")

    assert len(result['copied']) == 10

    for i in range(1, 11):
        target_path = os.path.join(target, *[f'level{j}' for j in range(1, i + 1)], 'file.txt')
        assert os.path.exists(target_path), f"缺失文件: {target_path}"

    diff_after = compare_folders(source, target)
    assert len(diff_after['deleted']) == 0

    print("✅ 深层嵌套同步测试通过!")
    print()

    shutil.rmtree(base_dir)


def main():
    test_compare()
    test_sync_dry_run()
    test_sync_copy_only()
    test_sync_full()
    test_sync_deep_nested()

    print("=" * 60)
    print("🎉 所有测试全部通过!")
    print("=" * 60)


if __name__ == '__main__':
    main()
