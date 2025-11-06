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
                logger.warning(f"Unsupported operator: {rule.operator}", extra=self.get_log_extra())
                return False
            
            op_func = self.OPERATORS[rule.operator]
            
            # 对于is_empty和is_not_empty操作符，不需要比较值
            if rule.operator in ["is_empty", "is_not_empty"]:
                return op_func(field_value, None)
            
            return op_func(field_value, rule.value)
            
        except Exception as e:
            logger.error(f"Error evaluating rule: {str(e)}", extra=self.get_log_extra())
            return False
    
    def _parse_rules(self, rules_data: Any) -> List[SwitchRule]:
        """解析规则配置"""
        import json
        
        # 如果rules_data是字符串，尝试解析为JSON
        if isinstance(rules_data, str):
            try:
                rules_data = json.loads(rules_data)
            except json.JSONDecodeError as e:
                logger.error(f"Error parsing rules JSON: {str(e)}", extra=self.get_log_extra())
                return []
        
        # 确保rules_data是列表
        if not isinstance(rules_data, list):
            logger.error(f"Rules data must be a list, got {type(rules_data)}", extra=self.get_log_extra())
            return []
        
        rules = []
        for i, rule_data in enumerate(rules_data):
            try:
                # 确保rule_data是字典
                if not isinstance(rule_data, dict):
                    logger.error(f"Rule {i} must be a dictionary, got {type(rule_data)}", extra=self.get_log_extra())
                    continue
                
                rule = SwitchRule(
                    field=rule_data.get("field", ""),
                    operator=rule_data.get("operator", "equals"),
                    value=rule_data.get("value"),
                    output_index=rule_data.get("output_index", i % self.output_count)
                )
                rules.append(rule)
            except Exception as e:
                logger.error(f"Error parsing rule {i}: {str(e)}", extra=self.get_log_extra())
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
                    
                    logger.info(f"SwitchNode: Rule matched, activating {output_key}", extra=self.get_log_extra())
                    
                    # 如果是first_match模式，找到第一个匹配就停止
                    if mode == "first_match":
                        break
        
        # 如果没有任何匹配，使用fallback
        if not matched_outputs:
            outputs["fallback"] = data
            logger.info("SwitchNode: No rules matched, using fallback", extra=self.get_log_extra())
        
        # 记录哪些输出端口被激活
        active_outputs = [k for k, v in outputs.items() if v is not None]
        logger.info(f"SwitchNode: Active outputs: {active_outputs}", extra=self.get_log_extra())
        
        return outputs


class PassThroughNode(WorkflowNode):
    """透传节点 - 用于数据流控制和透传
    
    主要用途：
    - 接收真正的数据参数和控制信号
    - 只有当控制信号存在（非None）时才透传数据
    - 解决SwitchNode等控制节点的输出控制问题
    - 确保工作流的正确执行顺序
    
    典型使用场景：
    SwitchNode -> PassThroughNode -> 后续节点
    其中SwitchNode的输出作为控制信号，真正的数据通过PassThroughNode透传
    """
    
    category = "control"
    
    def __init__(self, node_id: Optional[str] = None):
        super().__init__(node_id)
        
        # 输入端口
        self.add_input_port("data", "any", True, tooltip="要透传的真实数据")
        self.add_input_port("control", "any", False, None, 
                          tooltip="控制信号，当此信号存在（非None）时才透传数据")
        self.add_input_port("pass_on_empty", "boolean", False, False,
                          tooltip="当控制信号为空时是否仍然透传数据")
        
        # 输出端口
        self.add_output_port("output", "any", tooltip="透传的数据输出")
    
    async def process(self) -> Dict[str, Any]:
        """处理透传逻辑"""
        if not self.validate_inputs():
            raise ValueError("Required inputs missing")
        
        data = self.input_values["data"]
        control = self.input_values.get("control")
        pass_on_empty = self.input_values.get("pass_on_empty", False)
        
        # 判断是否应该透传数据
        should_pass = False
        
        if control is not None:
            # 控制信号存在，透传数据
            should_pass = True
            logger.info("PassThroughNode: Control signal present, passing data through", extra=self.get_log_extra())
        elif pass_on_empty:
            # 控制信号为空但设置了pass_on_empty，仍然透传
            should_pass = True
            logger.info("PassThroughNode: Control signal empty but pass_on_empty=True, passing data through", extra=self.get_log_extra())
        else:
            # 控制信号为空且不允许空透传，阻止数据流
            logger.info("PassThroughNode: Control signal empty and pass_on_empty=False, blocking data flow", extra=self.get_log_extra())
        
        return {
            "output": data if should_pass else None
        }


# 使用示例：
"""
# ===== SwitchNode 使用示例 =====
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


# ===== PassThroughNode 使用示例 =====

# 场景1: 与SwitchNode配合使用
# 创建工作流节点
switch_node = SwitchNode(output_count=2)
passthrough_node = PassThroughNode()

# 原始数据（真正要处理的数据）
original_data = {
    "user_id": 12345,
    "action": "purchase",
    "amount": 100.0,
    "timestamp": "2024-01-01T10:00:00Z"
}

# Switch节点配置
switch_node.input_values = {
    "data": {"user_type": "premium"},  # 用于路由判断的数据
    "rules": [
        {
            "field": "user_type",
            "operator": "equals",
            "value": "premium",
            "output_index": 0
        }
    ],
    "mode": "first_match"
}

# 执行Switch节点
switch_result = await switch_node.process()
# switch_result = {
#     "output_0": {"user_type": "premium"},  # 匹配的输出
#     "output_1": None,
#     "fallback": None
# }

# PassThrough节点配置
passthrough_node.input_values = {
    "data": original_data,  # 真正要透传的数据
    "control": switch_result["output_0"],  # Switch节点的输出作为控制信号
    "pass_on_empty": False
}

# 执行PassThrough节点
passthrough_result = await passthrough_node.process()
# passthrough_result = {
#     "output": {
#         "user_id": 12345,
#         "action": "purchase", 
#         "amount": 100.0,
#         "timestamp": "2024-01-01T10:00:00Z"
#     }
# }

# 场景2: 条件数据流控制
passthrough_node2 = PassThroughNode()
passthrough_node2.input_values = {
    "data": {"message": "Hello World"},
    "control": None,  # 无控制信号
    "pass_on_empty": False  # 不允许空透传
}

result2 = await passthrough_node2.process()
# result2 = {"output": None}  # 数据被阻止

# 场景3: 允许空透传
passthrough_node3 = PassThroughNode()
passthrough_node3.input_values = {
    "data": {"message": "Always pass"},
    "control": None,
    "pass_on_empty": True  # 允许空透传
}

result3 = await passthrough_node3.process()
# result3 = {"output": {"message": "Always pass"}}  # 数据被透传

# 典型工作流结构：
# [数据源] -> [Switch节点] -> [PassThrough节点] -> [后续处理节点]
#     |                           ^
#     +---> [真实数据] -----------+
#
# 这样可以确保：
# 1. Switch节点控制工作流走向
# 2. 真实数据通过PassThrough节点透传
# 3. 只有满足条件的分支才会继续执行
"""