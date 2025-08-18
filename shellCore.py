import os
import sys
import fnmatch
import stat

def print_output(data, max_lines=20):
    """智能打印输出，支持列表和字典格式化"""
    if isinstance(data, dict):
        print("{")
        for i, (k, v) in enumerate(data.items()):
            if i >= max_lines:
                print(f"  ... (共 {len(data)} 项)")
                break
            print(f"  {k}: {v}")
        print("}")
    
    elif isinstance(data, list) or isinstance(data, tuple):
        print("[")
        for i, item in enumerate(data):
            if i >= max_lines:
                print(f"  ... (共 {len(data)} 项)")
                break
            print(f"  {item}")
        print("]")
    
    elif isinstance(data, str) and '\n' in data:
        lines = data.split('\n')
        for i, line in enumerate(lines):
            if i >= max_lines:
                print(f"... (共 {len(lines)} 行)")
                break
            print(line)
    
    else:
        print(data)

def get_permission_help():
    """权限系统帮助文档"""
    return ("""
文件权限管理系统 (u 命令)

使用格式: :ru
输入格式: <文件/目录> <权限码>

权限码格式:
  4位数字格式: [特殊权限][用户权限][组权限][其他权限]
  3位数字格式: [用户权限][组权限][其他权限]
  2位数字格式: [用户权限][组权限] (其他权限默认为0)
  1位数字格式: [用户权限] (组和其他权限默认为0)

基本权限值:
  0 = ---
  1 = --x
  2 = -w-
  3 = -wx
  4 = r--
  5 = r-x
  6 = rw-
  7 = rwx

特殊权限值:
  4 = setuid (s)
  2 = setgid (s)
  1 = sticky bit (t)

常用权限码示例:
  600 = (rw-------)    用户读写
  644 = (rw-r--r--)   用户读写，其他读取
  755 = (rwxr-xr-x)  用户完全访问，其他读取执行
  700 = (rwx------)   用户完全访问
  1777 = (rwxrwxrwt) 粘滞位全访问 (临时文件目录)
  4755 = (rwsr-xr-x) setuid可执行程序

批量操作:
  使用通配符 * 和 ? 支持批量修改
  示例: *.txt 644  或  image* 644
""")

def get_human_permissions(filepath: str) -> str:
    """获取人类可读的权限字符串"""
    st = os.stat(filepath)
    perms = ['-'] * 10
    
    # 文件类型
    if stat.S_ISDIR(st.st_mode):
        perms[0] = 'd'
    elif stat.S_ISLNK(st.st_mode):
        perms[0] = 'l'
    
    # 权限转换
    permission_map = {
        0: '---', 1: '--x', 2: '-w-', 3: '-wx',
        4: 'r--', 5: 'r-x', 6: 'rw-', 7: 'rwx'
    }
    
    # 用户权限
    perm_val = (st.st_mode & 0o700) >> 6
    perms[1:4] = list(permission_map.get(perm_val, '---'))
    
    # 组权限
    perm_val = (st.st_mode & 0o070) >> 3
    perms[4:7] = list(permission_map.get(perm_val, '---'))
    
    # 其他权限
    perm_val = st.st_mode & 0o007
    perms[7:10] = list(permission_map.get(perm_val, '---'))
    
    # 特殊权限位
    if st.st_mode & stat.S_ISUID:
        perms[3] = 's' if perms[3] == 'x' else 'S'
    if st.st_mode & stat.S_ISGID:
        perms[6] = 's' if perms[6] == 'x' else 'S'
    if st.st_mode & stat.S_ISVTX:
        perms[9] = 't' if perms[9] == 'x' else 'T'
    
    return ''.join(perms)

def batch_modify_permissions(pattern: str, perm_code: str, directory: str) -> str:
    """批量修改匹配文件的权限"""
    try:
        # 验证权限码
        if not perm_code.isdigit() or len(perm_code) not in (1, 2, 3, 4):
            return f"错误: 无效权限码 '{perm_code}'，应为 1-4 位数字"
        perm_octal = int(perm_code, 8)
        
        # 获取目录中所有匹配文件
        files = []
        for filename in os.listdir(directory):
            if filename == pattern or fnmatch.fnmatch(filename, pattern):
                files.append(filename)
        
        if not files:
            return f"未找到匹配文件: {pattern}"
        
        # 应用权限修改到所有匹配文件
        results = []
        for filename in files:
            filepath = os.path.join(directory, filename)
            try:
                os.chmod(filepath, perm_octal)
                new_perm = get_human_permissions(filepath)
                results.append(f"{filename}: {new_perm} ({perm_code})")
            except Exception as e:
                results.append(f"{filename}: 错误 - {str(e)}")
        
        return "\n".join([f"批量权限修改结果 ({len(files)} 个文件):"] + results)
    
    except Exception as e:
        return f"批量操作错误: {str(e)}"

def find_files(pattern: str, search_dir: str) -> list:
    """根据模式查找目录中的文件（不区分大小写，支持通配符）"""
    # 获取目标目录下的所有文件名
    try:
        filenames = os.listdir(search_dir)
    except FileNotFoundError:
        return [f"错误: 目录不存在 - {search_dir}"]
    except PermissionError:
        return [f"错误: 无访问权限 - {search_dir}"]
    
    # 模式为空时返回所有文件
    if not pattern:
        return filenames
    
    # 创建不区分大小写的匹配函数
    def match_case_insensitive(filename):
        # 方法1: 使用fnmatch处理简单通配符
        if '*' in pattern or '?' in pattern or '[' in pattern:
            return fnmatch.fnmatch(filename.lower(), pattern.lower())
        
        # 方法2: 处理基本文本查找（当不包含通配符时）
        return pattern.lower() in filename.lower()
    
    # 筛选匹配的文件
    return [f for f in filenames if match_case_insensitive(f)]

def delete_target(target: str, current_path: str) -> str:
    """安全删除文件或目录（带确认）"""
    if not target:
        return "错误: 未提供删除目标"
    
    try:
        # 支持通配符 (*?) 扩展
        if '*' in target or '?' in target:
            return batch_delete(target, current_path)
        
        # 完整路径处理
        full_path = os.path.join(current_path, target)
        
        # 验证路径是否存在
        if not os.path.exists(full_path):
            return f"错误: 目标不存在 - {target}"
        
        # 判断是文件还是目录
        if os.path.isfile(full_path):
            return delete_file(full_path, target)
        elif os.path.isdir(full_path):
            return delete_directory(full_path, target)
        else:
            return f"错误: 未知的目标类型 - {target}"
    
    except Exception as e:
        return f"删除错误: {str(e)}"

def delete_file(file_path: str, display_name: str) -> str:
    """删除文件（带确认）"""
    # 获取文件信息
    file_size = os.path.getsize(file_path)
    human_size = format_file_size(file_size)
    
    # 确认提示
    confirm = input(f"确认删除文件 '{display_name}' ({human_size})? [y/N]: ").strip().lower()
    if confirm != 'y':
        return f"取消删除: {display_name}"
    
    # 执行删除
    os.remove(file_path)
    return f"文件已删除: {display_name}"

def delete_directory(dir_path: str, display_name: str) -> str:
    """删除目录（带确认）"""
    # 获取目录信息
    try:
        item_count = count_directory_items(dir_path)
    except Exception as e:
        return f"错误: 无法统计目录内容 - {str(e)}"
    
    # 确认提示
    confirm = input(f"确认删除目录 '{display_name}' (包含 {item_count} 个文件和目录)? [y/N]: ").strip().lower()
    if confirm != 'y':
        return f"取消删除: {display_name}"
    
    try:
        # 尝试递归删除目录
        shutil.rmtree(dir_path)
        return f"目录已删除: {display_name} (包含 {item_count} 个项目)"
    except Exception as e:
        # 处理删除失败的情况
        return f"删除目录失败: {str(e)}"

def batch_delete(pattern: str, current_path: str) -> str:
    """批量删除匹配的文件和目录（带确认）"""
    try:
        # 获取目录中所有匹配文件
        matches = []
        for filename in os.listdir(current_path):
            if filename == pattern or fnmatch.fnmatch(filename, pattern):
                matches.append(filename)
        
        if not matches:
            return f"未找到匹配目标: {pattern}"
        
        # 显示匹配结果
        print(f"找到 {len(matches)} 个匹配目标:")
        for i, match in enumerate(matches, 1):
            print(f"  {i}. {match}")
        
        # 确认提示
        confirm = input(f"确认删除以上 {len(matches)} 个目标? [y/N]: ").strip().lower()
        if confirm != 'y':
            return f"取消批量删除: {pattern}"
        
        # 逐个删除目标
        results = []
        for target in matches:
            full_path = os.path.join(current_path, target)
            
            try:
                if os.path.isfile(full_path):
                    # 删除文件
                    os.remove(full_path)
                    results.append(f"文件已删除: {target}")
                elif os.path.isdir(full_path):
                    # 删除目录
                    shutil.rmtree(full_path)
                    results.append(f"目录已删除: {target}")
                else:
                    results.append(f"错误: 未知类型 - {target}")
            except Exception as e:
                results.append(f"删除失败: {target} - {str(e)}")
        
        return "\n".join([f"批量删除结果 ({len(matches)} 个目标):"] + results)
    
    except Exception as e:
        return f"批量删除错误: {str(e)}"

def format_file_size(size: int) -> str:
    """格式化文件大小为人类可读格式"""
    if size < 1024:
        return f"{size} B"
    elif size < 1024**2:
        return f"{size/1024:.1f} KB"
    elif size < 1024**3:
        return f"{size/(1024**2):.1f} MB"
    else:
        return f"{size/(1024**3):.1f} GB"

def count_directory_items(dir_path: str) -> int:
    """计算目录中的项目总数（递归）"""
    count = 0
    for root, dirs, files in os.walk(dir_path):
        # 添加只读文件处理
        for file in files:
            file_path = os.path.join(root, file)
            try:
                # 确保文件可写
                if not os.access(file_path, os.W_OK):
                    os.chmod(file_path, stat.S_IWUSR)
            except:
                pass  # 如果无法更改权限，继续执行
        
        count += len(dirs) + len(files)
    return count
def create_file(file_path: str, current_path: str) -> str:
    """创建新文件或更新现有文件的修改时间"""
    if not file_path:
        return "错误: 未提供文件名"
    
    try:
        # 获取完整路径
        full_path = os.path.join(current_path, file_path)
        
        # 如果文件已存在，更新修改时间
        if os.path.exists(full_path):
            # 更新修改时间
            os.utime(full_path, None)
            return f"文件已更新: {file_path} (修改时间已刷新)"
        
        # 创建新文件
        with open(full_path, 'w') as f:
            pass  # 创建空文件
        
        # 设置默认权限 (644)
        os.chmod(full_path, 0o644)
        
        return f"文件已创建: {file_path} (权限: {get_human_permissions(full_path)})"
    
    except Exception as e:
        return f"创建文件错误: {str(e)}"

def create_directory(dir_path: str, current_path: str) -> str:
    """创建新目录（支持多级目录）"""
    if not dir_path:
        return "错误: 未提供目录名"
    
    try:
        # 获取完整路径
        full_path = os.path.join(current_path, dir_path)
        
        # 如果目录已存在
        if os.path.exists(full_path):
            if os.path.isdir(full_path):
                return f"目录已存在: {dir_path}"
            return f"错误: 路径已存在但不是目录 - {dir_path}"
        
        # 创建目录（包括所有父目录）
        os.makedirs(full_path, exist_ok=True)
        
        # 设置默认权限 (755)
        os.chmod(full_path, 0o755)
        
        return f"目录已创建: {dir_path} (权限: {get_human_permissions(full_path)})"
    
    except Exception as e:
        return f"创建目录错误: {str(e)}"
def modify_file_permissions(target: str, file_list=None, current_path: str = '') -> str:
    """支持列表输入和交互式权限码输入的文件权限管理工具"""
    # 默认帮助信息
    if not target and file_list is None:
        return get_permission_help()
    
    try:
        # 情况1: 有文件列表输入 (来自前一个命令如 :m)
        if file_list is not None:
            # 文件列表必须是可迭代的
            if not isinstance(file_list, (list, tuple)):
                return "错误: 输入应为文件列表"
                
            # 请求权限码
            perm_code = input("请输入权限码: ").strip()
            if not perm_code.isdigit() or len(perm_code) not in (1, 2, 3, 4):
                return f"错误: 无效权限码 '{perm_code}'，应为 1-4 位数字"
            
            # 转换权限码为八进制
            perm_octal = int(perm_code, 8)
            
            # 处理列表中的每个文件
            results = []
            for item in file_list:
                # 处理文件路径格式
                if isinstance(item, (str, bytes)):
                    file_name = str(item)
                else:
                    file_name = str(item)
                
                # 获取完整路径
                full_path = os.path.join(current_path, file_name)
                
                if not os.path.exists(full_path):
                    results.append(f"错误: 文件不存在 - {file_name}")
                    continue
                
                # 应用权限修改
                os.chmod(full_path, perm_octal)
                
                # 获取修改后权限
                new_perm = get_human_permissions(full_path)
                results.append(f"{file_name}: {new_perm} ({perm_code})")
            
            return "\n".join(results)
        
        # 情况2: 直接命令格式 "文件名/目录名 权限码"
        parts = target.strip().rsplit(' ', 1)
        if len(parts) < 2:
            return get_permission_help()
        
        target_path = parts[0].strip()
        perm_code = parts[1].strip()
        
        # 支持通配符 (*?) 扩展
        if '*' in target_path or '?' in target_path:
            return batch_modify_permissions(target_path, perm_code, current_path)
        
        # 完整路径处理
        full_path = os.path.join(current_path, target_path)
        
        # 权限码验证
        if not perm_code.isdigit() or len(perm_code) not in (1, 2, 3, 4):
            return f"错误: 无效权限码 '{perm_code}'，应为 1-4 位数字"
        
        # 转换权限码为八进制
        perm_octal = int(perm_code, 8)
        
        # 验证路径是否存在
        if not os.path.exists(full_path):
            return f"错误: 目标不存在 - {target_path}"
        
        # 应用权限修改
        os.chmod(full_path, perm_octal)
        
        # 获取修改后权限
        new_perm = get_human_permissions(full_path)
        
        return f"权限成功修改: {target_path} -> {new_perm} ({perm_code})"
    
    except Exception as e:
        return f"权限修改错误: {str(e)}"

def execute_composite_command(cmd: str, initial_state: dict) -> dict:
    """执行组合命令：冒号+字母序列"""
    if not cmd.startswith(':'):
        return initial_state
    
    state = initial_state
    for action in cmd[1:]:
        if action in command_functions:
            try:
                state = command_functions[action](state)
            except Exception as e:
                print(f"执行 {action} 出错: {e}")
        else:
            print(f"未知命令: :{action}")
            break
    return state

def execute_command(cmd: str, initial_state: dict = None) -> dict:
    """执行单个命令并返回结果状态"""
    if initial_state is None:
        initial_state = {'input': '', 'output': None, 'user_input': '', 'path': os.getcwd()}
    
    return execute_composite_command(cmd, initial_state)

# 扩展命令函数映射表（修复版）
command_functions = {
    # 基础功能（修复 r 命令）
    'p': lambda s: {**s, 'output': print_output(s.get('output', '')) or s.get('output', '')},
    'i': lambda s: {**s, 'output': os.getcwd()},
    'r': lambda s: {**s, 'user_input': input("输入: "), 'input': s.get('output', '')},
    'g': lambda s: {
        # 优先使用user_input作为目录路径
        'path': s.get('user_input', '') or s.get('output', ''),
        'result': os.chdir(s.get('user_input', '') or s.get('output', '')) if s.get('user_input', '') or s.get('output', '') else None,
        'output': f"已切换到: {os.getcwd()}" if s.get('user_input', '') or s.get('output', '') else "错误: 未提供目录路径",
        'user_input': s.get('user_input', '')
    },
    'l': lambda s: {**s, 'output': os.listdir(s.get('path', '.'))},
    
    # 查找功能 m（修复匹配逻辑）
    'm': lambda s: {
        **s,
        'output': find_files(
            pattern=s.get('user_input', '') or s.get('input', ''),  # 优先使用user_input
            search_dir=s.get('path', os.getcwd())  # 使用当前工作目录
        )
    },
    
    # 文件权限管理命令 :u
    'u': lambda s: {
        **s,
        'output': modify_file_permissions(
            target=s.get('user_input', ''),  # 从 input 获取操作指令
            file_list=s.get('output', None),  # 文件列表支持
            current_path=s.get('path', os.getcwd())  # 当前工作目录
        )
    },
    't': lambda s: {
        **s,
        'output': create_file(
            file_path=s.get('user_input', '') or s.get('input', ''),
            current_path=s.get('path', os.getcwd())
        )
    },
    
    # 创建目录命令 (directory)
    'd': lambda s: {
        **s,
        'output': create_directory(
            dir_path=s.get('user_input', '') or s.get('input', ''),
            current_path=s.get('path', os.getcwd())
        )
    },
    # 其他功能保持不变...
    'f': lambda s: {**s, 'output': open(s.get('user_input', ''), 'r', encoding='utf-8').read() if s.get('user_input', '') else "错误: 未指定文件"},
    'w': lambda s: (open('output.txt','w', encoding='utf-8').write(str(s.get('output',''))), s),
    's': lambda s: {**s, 'output': str(s.get('output', ''))},
    'n': lambda s: {**s, 'output': len(s.get('output', []))},
    'x': lambda s: {
        **s,
        'output': delete_target(
            target=s.get('user_input', '') or s.get('input', ''),
            current_path=s.get('path', os.getcwd())
        )
    },
    'c': lambda s: {**s, 'output': os.path.exists(s.get('user_input', ''))},
    'e': lambda s: {**s, 'output': s.get('user_input', '') in os.environ},
    '?': lambda s: {**s, 'output': s}  # 状态查看
}