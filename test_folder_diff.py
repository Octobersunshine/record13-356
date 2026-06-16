import os
import shutil
import tempfile
from folder_diff import compare_folders, format_result


def create_test_file(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)


def main():
    base_dir = tempfile.mkdtemp(prefix='folder_diff_test_')
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

    print(f"测试文件夹:")
    print(f"  原始文件夹 (v1): {left}")
    print(f"  目标文件夹 (v2): {right}")
    print()

    result = compare_folders(left, right)
    print(format_result(result))
    print()

    def p(*parts):
        return os.path.join(*parts)

    assert p('added.txt') in result['added']
    assert p('only_in_right', 'deep', 'nested.txt') in result['added']
    assert p('subdir', 'file3.txt') in result['added']
    assert len(result['added']) == 3, f"预期3个新增，实际{len(result['added'])}个"

    assert p('deleted.txt') in result['deleted']
    assert p('only_in_left', 'deep', 'nested.txt') in result['deleted']
    assert p('subdir', 'file2.txt') in result['deleted']
    assert len(result['deleted']) == 3, f"预期3个删除，实际{len(result['deleted'])}个"

    assert p('modified.txt') in result['modified']
    assert len(result['modified']) == 1, f"预期1个修改，实际{len(result['modified'])}个"

    assert p('common.txt') not in result['added']
    assert p('common.txt') not in result['deleted']
    assert p('common.txt') not in result['modified']
    assert p('subdir', 'file1.txt') not in result['added']
    assert p('subdir', 'file1.txt') not in result['deleted']
    assert p('subdir', 'file1.txt') not in result['modified']

    print("✅ 所有测试通过!")

    shutil.rmtree(base_dir)


if __name__ == '__main__':
    main()
