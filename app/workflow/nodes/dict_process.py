
from app.workflow.base import WorkflowNode
from typing import Dict, Any

class DictCreateNode(WorkflowNode):
    """创建一个新的字典对象"""
    
    category = "dict_process"
    
    def __init__(self, node_id: str = None):
        super().__init__(node_id)
        
        # 输入端口（可选）
        self.add_input_port("initial_data", "object", False, tooltip="初始数据（可选）")
        
        # 输出端口
        self.add_output_port("dict", "object", tooltip="创建的字典对象")
    
    async def process(self) -> Dict[str, Any]:
        """创建新字典"""
        try:
            # 获取初始数据
            initial_data = self.input_values.get("initial_data", {})
            
            # 如果初始数据不是字典，创建空字典
            if not isinstance(initial_data, dict):
                result_dict = {}
            else:
                result_dict = initial_data.copy()
            
            return {
                "dict": result_dict
            }
                    
        except Exception as e:
            raise Exception(f"Error creating dictionary: {str(e)}")


class DictAddNode(WorkflowNode):
    """向字典中添加键值对"""
    
    category = "dict_process"
    
    def __init__(self, node_id: str = None):
        super().__init__(node_id)
        
        # 输入端口
        self.add_input_port("dict", "object", True, tooltip="目标字典")
        self.add_input_port("key", "string", True, tooltip="要添加的键")
        self.add_input_port("value", "any", True, tooltip="要添加的值")
        
        # 输出端口
        self.add_output_port("updated_dict", "object", tooltip="更新后的字典")
    
    async def process(self) -> Dict[str, Any]:
        """向字典添加键值对"""
        if not self.validate_inputs():
            raise ValueError("Required inputs missing")
            
        try:
            dict_obj = self.input_values["dict"]
            key = self.input_values["key"]
            value = self.input_values["value"]
            
            # 验证输入是字典
            if not isinstance(dict_obj, dict):
                raise ValueError("dict must be a dictionary")
            
            # 创建副本并添加键值对
            updated_dict = dict_obj.copy()
            updated_dict[key] = value
            
            return {
                "updated_dict": updated_dict
            }
                    
        except Exception as e:
            raise Exception(f"Error adding to dictionary: {str(e)}")


class DictGetNode(WorkflowNode):
    """从字典中获取指定键的值"""
    
    category = "dict_process"
    
    def __init__(self, node_id: str = None):
        super().__init__(node_id)
        
        # 输入端口
        self.add_input_port("dict", "object", True, tooltip="源字典")
        self.add_input_port("key", "string", True, tooltip="要获取的键")
        self.add_input_port("default_value", "any", False, tooltip="默认值（键不存在时返回）")
        
        # 输出端口
        self.add_output_port("value", "any", tooltip="获取的值")
        self.add_output_port("exists", "boolean", tooltip="键是否存在")
    
    async def process(self) -> Dict[str, Any]:
        """从字典获取值"""
        if not self.validate_inputs():
            raise ValueError("Required inputs missing")
            
        try:
            dict_obj = self.input_values["dict"]
            key = self.input_values["key"]
            default_value = self.input_values.get("default_value", None)
            
            # 验证输入是字典
            if not isinstance(dict_obj, dict):
                raise ValueError("dict must be a dictionary")
            
            # 检查键是否存在
            exists = key in dict_obj
            
            # 获取值
            if exists:
                value = dict_obj[key]
            else:
                value = default_value
            
            return {
                "value": value,
                "exists": exists
            }
                    
        except Exception as e:
            raise Exception(f"Error getting value from dictionary: {str(e)}")


class DictMergeNode(WorkflowNode):
    """合并多个字典"""
    
    category = "dict_process"
    
    def __init__(self, node_id: str = None):
        super().__init__(node_id)
        
        # 输入端口
        self.add_input_port("dict1", "object", True, tooltip="第一个字典")
        self.add_input_port("dict2", "object", True, tooltip="第二个字典")
        self.add_input_port("dict3", "object", False, tooltip="第三个字典（可选）")
        self.add_input_port("overwrite", "boolean", False, tooltip="是否覆盖重复键（默认True）")
        
        # 输出端口
        self.add_output_port("merged_dict", "object", tooltip="合并后的字典")
    
    async def process(self) -> Dict[str, Any]:
        """合并字典"""
        if not self.validate_inputs():
            raise ValueError("Required inputs missing")
            
        try:
            dict1 = self.input_values["dict1"]
            dict2 = self.input_values["dict2"]
            dict3 = self.input_values.get("dict3", {})
            overwrite = self.input_values.get("overwrite", True)
            
            # 验证输入都是字典
            if not isinstance(dict1, dict):
                raise ValueError("dict1 must be a dictionary")
            if not isinstance(dict2, dict):
                raise ValueError("dict2 must be a dictionary")
            if dict3 and not isinstance(dict3, dict):
                raise ValueError("dict3 must be a dictionary")
            
            # 开始合并
            merged_dict = dict1.copy()
            
            # 合并第二个字典
            if overwrite:
                merged_dict.update(dict2)
            else:
                for key, value in dict2.items():
                    if key not in merged_dict:
                        merged_dict[key] = value
            
            # 合并第三个字典（如果存在）
            if dict3:
                if overwrite:
                    merged_dict.update(dict3)
                else:
                    for key, value in dict3.items():
                        if key not in merged_dict:
                            merged_dict[key] = value
            
            return {
                "merged_dict": merged_dict
            }
                    
        except Exception as e:
            raise Exception(f"Error merging dictionaries: {str(e)}")


class DictKeysNode(WorkflowNode):
    """获取字典的所有键"""
    
    category = "dict_process"
    
    def __init__(self, node_id: str = None):
        super().__init__(node_id)
        
        # 输入端口
        self.add_input_port("dict", "object", True, tooltip="源字典")
        
        # 输出端口
        self.add_output_port("keys", "array", tooltip="字典的所有键")
        self.add_output_port("count", "number", tooltip="键的数量")
    
    async def process(self) -> Dict[str, Any]:
        """获取字典的所有键"""
        if not self.validate_inputs():
            raise ValueError("Required inputs missing")
            
        try:
            dict_obj = self.input_values["dict"]
            
            # 验证输入是字典
            if not isinstance(dict_obj, dict):
                raise ValueError("dict must be a dictionary")
            
            # 获取所有键
            keys = list(dict_obj.keys())
            
            return {
                "keys": keys,
                "count": len(keys)
            }
                    
        except Exception as e:
            raise Exception(f"Error getting dictionary keys: {str(e)}")


class DictValuesNode(WorkflowNode):
    """获取字典的所有值"""
    
    category = "dict_process"
    
    def __init__(self, node_id: str = None):
        super().__init__(node_id)
        
        # 输入端口
        self.add_input_port("dict", "object", True, tooltip="源字典")
        
        # 输出端口
        self.add_output_port("values", "array", tooltip="字典的所有值")
        self.add_output_port("count", "number", tooltip="值的数量")
    
    async def process(self) -> Dict[str, Any]:
        """获取字典的所有值"""
        if not self.validate_inputs():
            raise ValueError("Required inputs missing")
            
        try:
            dict_obj = self.input_values["dict"]
            
            # 验证输入是字典
            if not isinstance(dict_obj, dict):
                raise ValueError("dict must be a dictionary")
            
            # 获取所有值
            values = list(dict_obj.values())
            
            return {
                "values": values,
                "count": len(values)
            }
                    
        except Exception as e:
            raise Exception(f"Error getting dictionary values: {str(e)}")


class DictRemoveNode(WorkflowNode):
    """从字典中删除指定的键值对"""
    
    category = "dict_process"
    
    def __init__(self, node_id: str = None):
        super().__init__(node_id)
        
        # 输入端口
        self.add_input_port("dict", "object", True, tooltip="源字典")
        self.add_input_port("key", "string", True, tooltip="要删除的键")
        self.add_input_port("ignore_missing", "boolean", False, tooltip="忽略不存在的键（默认False）")
        
        # 输出端口
        self.add_output_port("updated_dict", "object", tooltip="删除后的字典")
        self.add_output_port("removed_value", "any", tooltip="被删除的值")
        self.add_output_port("was_removed", "boolean", tooltip="是否成功删除")
    
    async def process(self) -> Dict[str, Any]:
        """从字典删除键值对"""
        if not self.validate_inputs():
            raise ValueError("Required inputs missing")
            
        try:
            dict_obj = self.input_values["dict"]
            key = self.input_values["key"]
            ignore_missing = self.input_values.get("ignore_missing", False)
            
            # 验证输入是字典
            if not isinstance(dict_obj, dict):
                raise ValueError("dict must be a dictionary")
            
            # 创建副本
            updated_dict = dict_obj.copy()
            
            # 检查键是否存在
            if key in updated_dict:
                removed_value = updated_dict.pop(key)
                was_removed = True
            else:
                if not ignore_missing:
                    raise KeyError(f"Key '{key}' not found in dictionary")
                removed_value = None
                was_removed = False
            
            return {
                "updated_dict": updated_dict,
                "removed_value": removed_value,
                "was_removed": was_removed
            }
                    
        except Exception as e:
            raise Exception(f"Error removing from dictionary: {str(e)}")


class DictUpdateNode(WorkflowNode):
    """更新字典中指定键的值"""
    
    category = "dict_process"
    
    def __init__(self, node_id: str = None):
        super().__init__(node_id)
        
        # 输入端口
        self.add_input_port("dict", "object", True, tooltip="源字典")
        self.add_input_port("key", "string", True, tooltip="要更新的键")
        self.add_input_port("new_value", "any", True, tooltip="新值")
        self.add_input_port("create_if_missing", "boolean", False, tooltip="键不存在时是否创建（默认True）")
        
        # 输出端口
        self.add_output_port("updated_dict", "object", tooltip="更新后的字典")
        self.add_output_port("old_value", "any", tooltip="原来的值")
        self.add_output_port("was_updated", "boolean", tooltip="是否成功更新")
    
    async def process(self) -> Dict[str, Any]:
        """更新字典中的值"""
        if not self.validate_inputs():
            raise ValueError("Required inputs missing")
            
        try:
            dict_obj = self.input_values["dict"]
            key = self.input_values["key"]
            new_value = self.input_values["new_value"]
            create_if_missing = self.input_values.get("create_if_missing", True)
            
            # 验证输入是字典
            if not isinstance(dict_obj, dict):
                raise ValueError("dict must be a dictionary")
            
            # 创建副本
            updated_dict = dict_obj.copy()
            
            # 检查键是否存在
            if key in updated_dict:
                old_value = updated_dict[key]
                updated_dict[key] = new_value
                was_updated = True
            else:
                if create_if_missing:
                    old_value = None
                    updated_dict[key] = new_value
                    was_updated = True
                else:
                    raise KeyError(f"Key '{key}' not found in dictionary and create_if_missing is False")
            
            return {
                "updated_dict": updated_dict,
                "old_value": old_value,
                "was_updated": was_updated
            }
                    
        except Exception as e:
            raise Exception(f"Error updating dictionary: {str(e)}")


class DictClearNode(WorkflowNode):
    """清空字典的所有内容"""
    
    category = "dict_process"
    
    def __init__(self, node_id: str = None):
        super().__init__(node_id)
        
        # 输入端口
        self.add_input_port("dict", "object", True, tooltip="要清空的字典")
        
        # 输出端口
        self.add_output_port("empty_dict", "object", tooltip="清空后的字典")
        self.add_output_port("original_count", "number", tooltip="原字典的键数量")
    
    async def process(self) -> Dict[str, Any]:
        """清空字典"""
        if not self.validate_inputs():
            raise ValueError("Required inputs missing")
            
        try:
            dict_obj = self.input_values["dict"]
            
            # 验证输入是字典
            if not isinstance(dict_obj, dict):
                raise ValueError("dict must be a dictionary")
            
            # 记录原来的键数量
            original_count = len(dict_obj)
            
            # 创建空字典
            empty_dict = {}
            
            return {
                "empty_dict": empty_dict,
                "original_count": original_count
            }
                    
        except Exception as e:
            raise Exception(f"Error clearing dictionary: {str(e)}")


class DictCopyNode(WorkflowNode):
    """创建字典的副本"""
    
    category = "dict_process"
    
    def __init__(self, node_id: str = None):
        super().__init__(node_id)
        
        # 输入端口
        self.add_input_port("dict", "object", True, tooltip="要复制的字典")
        self.add_input_port("deep_copy", "boolean", False, tooltip="是否深度复制（默认False）")
        
        # 输出端口
        self.add_output_port("copied_dict", "object", tooltip="复制的字典")
    
    async def process(self) -> Dict[str, Any]:
        """复制字典"""
        if not self.validate_inputs():
            raise ValueError("Required inputs missing")
            
        try:
            dict_obj = self.input_values["dict"]
            deep_copy = self.input_values.get("deep_copy", False)
            
            # 验证输入是字典
            if not isinstance(dict_obj, dict):
                raise ValueError("dict must be a dictionary")
            
            # 复制字典
            if deep_copy:
                import copy
                copied_dict = copy.deepcopy(dict_obj)
            else:
                copied_dict = dict_obj.copy()
            
            return {
                "copied_dict": copied_dict
            }
                    
        except Exception as e:
            raise Exception(f"Error copying dictionary: {str(e)}")


class DictHasKeyNode(WorkflowNode):
    """检查字典是否包含指定的键"""
    
    category = "dict_process"
    
    def __init__(self, node_id: str = None):
        super().__init__(node_id)
        
        # 输入端口
        self.add_input_port("dict", "object", True, tooltip="要检查的字典")
        self.add_input_port("key", "string", True, tooltip="要检查的键")
        
        # 输出端口
        self.add_output_port("has_key", "boolean", tooltip="是否包含该键")
        self.add_output_port("value", "any", tooltip="键对应的值（如果存在）")
    
    async def process(self) -> Dict[str, Any]:
        """检查字典是否包含键"""
        if not self.validate_inputs():
            raise ValueError("Required inputs missing")
            
        try:
            dict_obj = self.input_values["dict"]
            key = self.input_values["key"]
            
            # 验证输入是字典
            if not isinstance(dict_obj, dict):
                raise ValueError("dict must be a dictionary")
            
            # 检查键是否存在
            has_key = key in dict_obj
            value = dict_obj.get(key) if has_key else None
            
            return {
                "has_key": has_key,
                "value": value
            }
                    
        except Exception as e:
            raise Exception(f"Error checking dictionary key: {str(e)}")

