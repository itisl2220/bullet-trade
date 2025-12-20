"""
策略参数提取工具

从策略文件中提取可配置的参数（g.变量）
"""

import ast
import re
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple


def extract_strategy_params(strategy_file: str) -> Dict[str, Dict[str, Any]]:
    """
    从策略文件中提取参数
    
    Args:
        strategy_file: 策略文件路径
        
    Returns:
        参数字典，格式为:
        {
            'param_name': {
                'type': 'str|int|float|list|bool',
                'default': default_value,
                'description': '参数描述（从注释中提取）',
                'line': line_number
            }
        }
    """
    strategy_path = Path(strategy_file)
    if not strategy_path.exists():
        return {}
    
    try:
        with open(strategy_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception:
        return {}
    
    params = {}
    
    # 方法1: 使用AST解析（更准确）
    try:
        tree = ast.parse(content, filename=str(strategy_path))
        params.update(_extract_from_ast(tree, content))
    except Exception:
        pass
    
    # 方法2: 使用正则表达式解析（作为补充，处理复杂情况）
    params.update(_extract_from_regex(content))
    
    return params


def _extract_from_ast(tree: ast.AST, content: str) -> Dict[str, Dict[str, Any]]:
    """从AST中提取参数"""
    params = {}
    lines = content.split('\n')
    
    class ParamVisitor(ast.NodeVisitor):
        def visit_Assign(self, node):
            # 查找 g.xxx = value 形式的赋值
            for target in node.targets:
                if isinstance(target, ast.Attribute):
                    if isinstance(target.value, ast.Name) and target.value.id == 'g':
                        param_name = target.attr
                        # 获取默认值
                        default_value = _eval_ast_node(node.value)
                        param_type = _infer_type(default_value)
                        
                        # 获取行号附近的注释作为描述
                        line_num = node.lineno - 1
                        description = _extract_comment(lines, line_num, param_name)
                        
                        params[param_name] = {
                            'type': param_type,
                            'default': default_value,
                            'description': description,
                            'line': node.lineno
                        }
    
    visitor = ParamVisitor()
    visitor.visit(tree)
    
    return params


def _extract_from_regex(content: str) -> Dict[str, Dict[str, Any]]:
    """使用正则表达式提取参数（补充方法）"""
    params = {}
    lines = content.split('\n')
    
    # 匹配 g.xxx = value 或 g['xxx'] = value
    patterns = [
        r'g\.(\w+)\s*=\s*(.+)',  # g.param = value
        r"g\['(\w+)'\]\s*=\s*(.+)",  # g['param'] = value
        r'g\["(\w+)"\]\s*=\s*(.+)',  # g["param"] = value
    ]
    
    for i, line in enumerate(lines):
        for pattern in patterns:
            match = re.search(pattern, line)
            if match:
                param_name = match.group(1)
                value_str = match.group(2).strip()
                
                # 如果AST已经提取过，跳过（AST更准确）
                if param_name in params:
                    continue
                
                # 处理多行列表（如 g.stocks = [\n  "000001.XSHE",\n  ...\n]）
                if value_str.strip().startswith('['):
                    # 收集多行列表内容
                    list_lines = [value_str]
                    bracket_count = value_str.count('[') - value_str.count(']')
                    j = i + 1
                    while bracket_count > 0 and j < len(lines):
                        list_lines.append(lines[j])
                        bracket_count += lines[j].count('[') - lines[j].count(']')
                        j += 1
                    
                    # 合并所有行
                    full_list_str = ' '.join(list_lines)
                    # 提取列表中的字符串元素
                    list_items = re.findall(r'["\']([^"\']+)["\']', full_list_str)
                    if list_items:
                        default_value = list_items
                        param_type = 'list'
                        description = _extract_comment(lines, i, param_name)
                        params[param_name] = {
                            'type': param_type,
                            'default': default_value,
                            'description': description or f"{param_name}列表",
                            'line': i + 1
                        }
                        continue
                
                # 处理单行列表参数（如 g.stocks = ["000001.XSHE", "600000.XSHG"]）
                if value_str.strip().startswith('[') and value_str.strip().endswith(']'):
                    # 尝试提取列表中的字符串元素
                    list_items = re.findall(r'["\']([^"\']+)["\']', value_str)
                    if list_items:
                        default_value = list_items
                        param_type = 'list'
                        description = _extract_comment(lines, i, param_name)
                        params[param_name] = {
                            'type': param_type,
                            'default': default_value,
                            'description': description or f"{param_name}列表",
                            'line': i + 1
                        }
                        continue
                
                # 处理函数调用，提取参数
                if 'get_index_stocks' in value_str:
                    # 提取索引代码
                    index_match = re.search(r'get_index_stocks\s*\(["\']([^"\']+)["\']', value_str)
                    if index_match:
                        default_value = index_match.group(1)
                        param_type = 'str'
                        description = _extract_comment(lines, i, param_name)
                        params[param_name] = {
                            'type': param_type,
                            'default': default_value,
                            'description': description or f"股票池索引代码（如：{default_value}）",
                            'line': i + 1
                        }
                        continue
                
                # 跳过其他复杂表达式
                if any(op in value_str for op in ['(', '{', 'list(', 'dict(']):
                    # 尝试提取简单值
                    simple_value = _extract_simple_value(value_str)
                    if simple_value is not None:
                        value_str = str(simple_value)
                    else:
                        continue  # 无法提取，跳过
                
                # 解析值
                default_value = _parse_value(value_str)
                if default_value is not None:
                    param_type = _infer_type(default_value)
                    description = _extract_comment(lines, i, param_name)
                    
                    params[param_name] = {
                        'type': param_type,
                        'default': default_value,
                        'description': description,
                        'line': i + 1
                    }
    
    return params


def _eval_ast_node(node: ast.AST) -> Any:
    """安全地评估AST节点"""
    try:
        if isinstance(node, ast.Constant):
            return node.value
        elif isinstance(node, ast.Str):  # Python < 3.8
            return node.s
        elif isinstance(node, ast.Num):  # Python < 3.8
            return node.n
        elif isinstance(node, ast.NameConstant):  # Python < 3.8
            return node.value
        elif isinstance(node, ast.List):
            return [_eval_ast_node(e) for e in node.elts]
        elif isinstance(node, ast.Tuple):
            return tuple(_eval_ast_node(e) for e in node.elts)
        elif isinstance(node, ast.Dict):
            return {_eval_ast_node(k): _eval_ast_node(v) for k, v in zip(node.keys, node.values)}
        elif isinstance(node, ast.UnaryOp):
            if isinstance(node.op, ast.USub):
                return -_eval_ast_node(node.operand)
            elif isinstance(node.op, ast.UAdd):
                return +_eval_ast_node(node.operand)
        elif isinstance(node, ast.Call):
            # 对于函数调用，尝试提取参数
            if isinstance(node.func, ast.Name):
                func_name = node.func.id
                if func_name == 'get_index_stocks':
                    # 返回第一个参数作为默认值（股票池索引代码）
                    if node.args:
                        index_code = _eval_ast_node(node.args[0])
                        return index_code if index_code else "000300.XSHG"
                    return "000300.XSHG"  # 默认值
            # 对于其他函数调用，返回None，让正则表达式处理
            return None
    except Exception:
        pass
    return None


def _parse_value(value_str: str) -> Any:
    """解析字符串值"""
    value_str = value_str.strip()
    
    # 移除行尾注释
    if '#' in value_str:
        value_str = value_str.split('#')[0].strip()
    
    # 尝试直接评估
    try:
        # 安全评估
        if value_str.startswith('"') or value_str.startswith("'"):
            return ast.literal_eval(value_str)
        elif value_str.lower() in ('true', 'false'):
            return value_str.lower() == 'true'
        elif value_str.replace('.', '').replace('-', '').isdigit():
            if '.' in value_str:
                return float(value_str)
            return int(value_str)
        else:
            return ast.literal_eval(value_str)
    except Exception:
        # 如果无法解析，返回字符串
        return value_str


def _extract_simple_value(value_str: str) -> Any:
    """从复杂表达式中提取简单值"""
    # 尝试提取字符串参数
    str_match = re.search(r'["\']([^"\']+)["\']', value_str)
    if str_match:
        return str_match.group(1)
    
    # 尝试提取数字
    num_match = re.search(r'(-?\d+\.?\d*)', value_str)
    if num_match:
        num_str = num_match.group(1)
        if '.' in num_str:
            return float(num_str)
        return int(num_str)
    
    return None


def _infer_type(value: Any) -> str:
    """推断参数类型"""
    if value is None:
        return 'str'
    if isinstance(value, bool):
        return 'bool'
    elif isinstance(value, int):
        return 'int'
    elif isinstance(value, float):
        return 'float'
    elif isinstance(value, (list, tuple)):
        return 'list'
    elif isinstance(value, dict):
        return 'dict'
    else:
        return 'str'


def _extract_comment(lines: List[str], line_num: int, param_name: str) -> str:
    """从注释中提取参数描述"""
    # 检查当前行和前后行的注释
    for offset in [0, -1, 1, -2, 2]:
        check_line = line_num + offset
        if 0 <= check_line < len(lines):
            line = lines[check_line].strip()
            # 查找包含参数名的注释
            if '#' in line and param_name.lower() in line.lower():
                comment = line.split('#', 1)[1].strip()
                # 移除参数名
                comment = re.sub(rf'\b{param_name}\b', '', comment, flags=re.IGNORECASE).strip()
                if comment:
                    return comment
            # 或者查找单独的注释行
            elif line.startswith('#') and param_name.lower() in line.lower():
                comment = line[1:].strip()
                comment = re.sub(rf'\b{param_name}\b', '', comment, flags=re.IGNORECASE).strip()
                if comment:
                    return comment
    
    # 如果没有找到，返回默认描述
    return f"{param_name}参数"


def apply_strategy_params(strategy_file: str, params: Dict[str, Any]) -> None:
    """
    将参数应用到策略的g对象中
    
    注意：这个函数需要在策略加载后、initialize调用前使用
    实际上，我们应该在引擎中传递参数，而不是修改文件
    
    Args:
        strategy_file: 策略文件路径
        params: 参数字典
    """
    from bullet_trade.core.globals import g
    
    for param_name, param_value in params.items():
        setattr(g, param_name, param_value)

