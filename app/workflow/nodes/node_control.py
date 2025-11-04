from typing import Dict, Any, List, Optional, TypeVar, Generic, Union
from dataclasses import dataclass
from abc import ABC, abstractmethod
from app.workflow.base import WorkflowNode
from app.utils.logger import logger
import re
import operator

@dataclass
class SwitchRule:
    """Switch节点的路由规则"""
    field: str  # 要检查的字段路径，支持点号分隔的嵌套路径
    operator: str  # 比较操作符
    value: Any  # 比较值
    output_index: int  # 匹配时的输出索引


class SwitchNode(WorkflowNode):
    """Switch节点 - 根据条件将数据路由到不同的输出端口
    
    类似于n8n的Switch节点，支持：
    - 基于字段值的条件匹配
    - 多种比较操作符（等于、不等于、大于、小于、包含、正则匹配等）
    - 多个输出端口
    - 默认输出（fallback）
    - 支持多个匹配或仅第一个匹配
    """
    
    category = "control"
    
    # 支持的操作符映射
    OPERATORS = {
        "equals": operator.eq,
        "not_equals": operator.ne,
        "greater": operator.gt,
        "greater_equal": operator.ge,
        "less": operator.lt,
        "less_equal": operator.le,
        "contains": lambda a, b: str(b) in str(a),
        "not_contains": lambda a, b: str(b) not in str(a),
        "starts_with": lambda a, b: str(a).startswith(str(b)),
        "ends_with": lambda a, b: str(a).endswith(str(b)),
        "regex": lambda a, b: bool(re.search(str(b), str(a))),
        "is_empty": lambda a, b: not a or (isinstance(a, (list, dict, str)) and len(a) == 0),
        "is_not_empty": lambda a, b: bool(a) and (not isinstance(a, (list, dict, str)) or len(a) > 0)
    }
    
    def __init__(self, node_id: Optional[str] = None, output_count: int = 2):
        super().__init__(node_id)
        
        # 输入端口
        self.add_input_port("data", "any", True, tooltip="要路由的输入数据")
        self.add_input_port("rules", "array", True, [], tooltip="路由规则列表")
        self.add_input_port("mode", "string", False, "first_match", 
                          options=["first_match", "all_matches"], 
                          tooltip="匹配模式：first_match=仅第一个匹配，all_matches=所有匹配")
        
        # 动态创建输出端口
        self.output_count = output_count
        for i in range(output_count):
            self.add_output_port(f"output_{i}", "any", tooltip=f"输出端口 {i}")
        
        # 默认输出端口（当没有规则匹配时）
        self.add_output_port("fallback", "any", tooltip="默认输出（无匹配时）")
    
    def _get_nested_value(self, data: Dict[str, Any], field_path: str) -> Any:
        """获取嵌套字段的值，支持点号分隔的路径"""
        try:
            value = data
            for key in field_path.split('.'):
                if isinstance(value, dict):
                    value = value.get(key)
                elif isinstance(value, list) and key.isdigit():
                    index = int(key)
                    value = value[index] if 0 <= index < len(value) else None
                else:
                    return None
            return value
        except (KeyError, IndexError, TypeError, ValueError):
            return None
    
    def _evaluate_rule(self, data: Dict[str, Any], rule: SwitchRule) -> bool:
        """评估单个规则是否匹配"""
        try:
            field_value = self._get_nested_value(data, rule.field)
            
            if rule.operator not in self.OPERATORS:
                logger.warning(f"Unsupported operator: {rule.operator}")
                return False
            
            op_func = self.OPERATORS[rule.operator]
            
            # 对于is_empty和is_not_empty操作符，不需要比较值
            if rule.operator in ["is_empty", "is_not_empty"]:
                return op_func(field_value, None)
            
            return op_func(field_value, rule.value)
            
        except Exception as e:
            logger.error(f"Error evaluating rule: {str(e)}")
            return False
    
    def _parse_rules(self, rules_data: Any) -> List[SwitchRule]:
        """解析规则配置"""
        import json
        
        # 如果rules_data是字符串，尝试解析为JSON
        if isinstance(rules_data, str):
            try:
                rules_data = json.loads(rules_data)
            except json.JSONDecodeError as e:
                logger.error(f"Error parsing rules JSON: {str(e)}")
                return []
        
        # 确保rules_data是列表
        if not isinstance(rules_data, list):
            logger.error(f"Rules data must be a list, got {type(rules_data)}")
            return []
        
        rules = []
        for i, rule_data in enumerate(rules_data):
            try:
                # 确保rule_data是字典
                if not isinstance(rule_data, dict):
                    logger.error(f"Rule {i} must be a dictionary, got {type(rule_data)}")
                    continue
                
                rule = SwitchRule(
                    field=rule_data.get("field", ""),
                    operator=rule_data.get("operator", "equals"),
                    value=rule_data.get("value"),
                    output_index=rule_data.get("output_index", i % self.output_count)
                )
                rules.append(rule)
            except Exception as e:
                logger.error(f"Error parsing rule {i}: {str(e)}")
        return rules
    
    async def process(self) -> Dict[str, Any]:
        """处理Switch逻辑"""
        if not self.validate_inputs():
            raise ValueError("Required inputs missing")
        
        data = self.input_values["data"]
        rules_data = self.input_values["rules"]
        mode = self.input_values.get("mode", "first_match")
        
        # 解析规则
        rules = self._parse_rules(rules_data)
        
        # 初始化所有输出为None（重要：None表示该分支不应执行）
        outputs = {}
        for i in range(self.output_count):
            outputs[f"output_{i}"] = None
        outputs["fallback"] = None
        
        matched_outputs = set()
        
        # 评估规则
        for rule in rules:
            if self._evaluate_rule(data, rule):
                output_key = f"output_{rule.output_index}"
                if output_key in outputs:
                    # 传递原始数据到匹配的分支
                    outputs[output_key] = data
                    matched_outputs.add(output_key)
                    
                    logger.info(f"SwitchNode: Rule matched, activating {output_key}")
                    
                    # 如果是first_match模式，找到第一个匹配就停止
                    if mode == "first_match":
                        break
        
        # 如果没有任何匹配，使用fallback
        if not matched_outputs:
            outputs["fallback"] = data
            logger.info("SwitchNode: No rules matched, using fallback")
        
        # 记录哪些输出端口被激活
        active_outputs = [k for k, v in outputs.items() if v is not None]
        logger.info(f"SwitchNode: Active outputs: {active_outputs}")
        
        return outputs


# 使用示例：
"""
# 创建Switch节点
switch_node = SwitchNode(output_count=3)

# 设置输入数据
switch_node.input_values = {
    "data": {
        "user": {"age": 25, "status": "active"},
        "score": 85,
        "category": "premium"
    },
    "rules": [
        {
            "field": "user.age",
            "operator": "greater_equal", 
            "value": 18,
            "output_index": 0  # 成年用户 -> output_0
        },
        {
            "field": "score",
            "operator": "greater",
            "value": 80,
            "output_index": 1  # 高分用户 -> output_1  
        },
        {
            "field": "category",
            "operator": "equals",
            "value": "premium",
            "output_index": 2  # 高级用户 -> output_2
        }
    ],
    "mode": "first_match"  # 或 "all_matches"
}

# 执行处理
result = await switch_node.process()

# 结果示例（first_match模式）：
# {
#     "output_0": {"user": {"age": 25, "status": "active"}, "score": 85, "category": "premium"},
#     "output_1": None,
#     "output_2": None, 
#     "fallback": None
# }

# 结果示例（all_matches模式）：
# {
#     "output_0": {"user": {"age": 25, "status": "active"}, "score": 85, "category": "premium"},
#     "output_1": {"user": {"age": 25, "status": "active"}, "score": 85, "category": "premium"},
#     "output_2": {"user": {"age": 25, "status": "active"}, "score": 85, "category": "premium"},
#     "fallback": None
# }

# 支持的操作符：
# - equals, not_equals: 等于/不等于
# - greater, greater_equal, less, less_equal: 数值比较
# - contains, not_contains: 包含/不包含（字符串）
# - starts_with, ends_with: 以...开始/结束
# - regex: 正则表达式匹配
# - is_empty, is_not_empty: 空值检查

# 字段路径支持：
# - "field": 直接字段
# - "user.name": 嵌套对象字段
# - "items.0": 数组索引访问
# - "user.addresses.0.city": 复杂嵌套路径
"""