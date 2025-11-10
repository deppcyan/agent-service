from typing import Dict, Any, List, Optional
from app.workflow.base import WorkflowNode
from app.utils.logger import logger
import asyncio


class SimpleForEachNode(WorkflowNode):
    """
    简化的 ForEach 节点，用于动态工作流执行
    
    对列表中的每个项目执行指定类型的节点，并收集所有结果。
    
    核心功能:
    - 遍历列表中的每个项目
    - 为每个项目执行指定的节点类型
    - 收集所有结果到列表中
    - 支持并行或串行执行
    - 完善的错误处理和报告
    
    使用场景:
    - 批量文本处理
    - 批量 API 调用
    - 数据转换管道
    - 并行模型推理
    """
    
    category = "control"
    
    def __init__(self, node_id: str = None):
        super().__init__(node_id)
        
        # 输入端口
        self.add_input_port("items", "array", True,
                           tooltip="要遍历的项目列表")
        self.add_input_port("node_type", "string", True,
                           tooltip="为每个项目执行的节点类名")
        self.add_input_port("item_port_name", "string", False, default_value="text",
                           tooltip="将项目传入的端口名称（默认: 'text'）")
        self.add_input_port("result_port_name", "string", False, default_value="result",
                           tooltip="收集结果的端口名称（默认: 'result'）")
        self.add_input_port("node_config", "object", False, default_value={},
                           tooltip="节点的额外配置参数")
        self.add_input_port("parallel", "boolean", False, default_value=False,
                           tooltip="是否并行执行")
        self.add_input_port("continue_on_error", "boolean", False, default_value=True,
                           tooltip="出错时是否继续处理")
        self.add_input_port("max_workers", "number", False,
                           tooltip="最大并发数（仅并行模式有效）")
        
        # 输出端口
        self.add_output_port("results", "array",
                            tooltip="所有迭代的结果列表")
        self.add_output_port("success_count", "number",
                            tooltip="成功处理的数量")
        self.add_output_port("error_count", "number",
                            tooltip="失败的数量")
        self.add_output_port("errors", "array",
                            tooltip="错误详情列表")
    
    async def _execute_single_item(self,
                                   item: Any,
                                   index: int,
                                   node_type: str,
                                   item_port_name: str,
                                   result_port_name: str,
                                   node_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行单个项目的处理
        
        Args:
            item: 要处理的项目
            index: 项目在列表中的索引
            node_type: 节点类名
            item_port_name: 输入端口名
            result_port_name: 输出端口名
            node_config: 额外配置
            
        Returns:
            包含 success, result, error, index, item 的字典
        """
        from app.workflow.registry import node_registry
        
        try:
            # 创建节点实例
            node = node_registry.create_node(node_type)
            node.task_id = self.task_id
            
            # 设置输入值
            node.input_values[item_port_name] = item
            
            # 应用额外配置
            for key, value in node_config.items():
                if key in node.input_ports:
                    node.input_values[key] = value
            
            # 执行节点
            result = await node.process()
            
            # 提取结果
            if result_port_name not in result:
                available_ports = ", ".join(result.keys())
                raise ValueError(
                    f"结果端口 '{result_port_name}' 未找到。"
                    f"可用端口: {available_ports}"
                )
            
            result_value = result[result_port_name]
            
            return {
                "success": True,
                "result": result_value,
                "error": None,
                "index": index,
                "item": item
            }
            
        except Exception as e:
            logger.error(
                f"ForEach 迭代 {index} 失败: {str(e)}",
                extra=self.get_log_extra()
            )
            return {
                "success": False,
                "result": None,
                "error": str(e),
                "index": index,
                "item": item
            }
    
    async def process(self) -> Dict[str, Any]:
        """处理所有项目"""
        if not self.validate_inputs():
            raise ValueError("缺少必需的输入")
        
        items = self.input_values["items"]
        node_type = self.input_values["node_type"]
        item_port_name = self.input_values.get("item_port_name", "text")
        result_port_name = self.input_values.get("result_port_name", "result")
        node_config = self.input_values.get("node_config", {})
        parallel = self.input_values.get("parallel", False)
        continue_on_error = self.input_values.get("continue_on_error", True)
        max_workers = self.input_values.get("max_workers")
        
        if not isinstance(items, list):
            raise ValueError("items 必须是列表类型")
        
        results = []
        errors = []
        success_count = 0
        error_count = 0
        
        logger.info(
            f"SimpleForEach 开始: 使用 {node_type} 处理 {len(items)} 个项目",
            extra=self.get_log_extra()
        )
        
        if parallel:
            # 并行执行，可选限制并发数
            if max_workers and max_workers > 0:
                # 使用信号量限制并发
                semaphore = asyncio.Semaphore(int(max_workers))
                
                async def bounded_task(item, index):
                    async with semaphore:
                        return await self._execute_single_item(
                            item, index, node_type,
                            item_port_name, result_port_name, node_config
                        )
                
                tasks = [
                    bounded_task(item, index)
                    for index, item in enumerate(items)
                ]
            else:
                # 无限制并行执行
                tasks = [
                    self._execute_single_item(
                        item, index, node_type,
                        item_port_name, result_port_name, node_config
                    )
                    for index, item in enumerate(items)
                ]
            
            iteration_results = await asyncio.gather(*tasks)
            
            # 处理结果
            for iter_result in iteration_results:
                if iter_result["success"]:
                    results.append(iter_result["result"])
                    success_count += 1
                else:
                    error_count += 1
                    errors.append({
                        "index": iter_result["index"],
                        "item": iter_result["item"],
                        "error": iter_result["error"]
                    })
        else:
            # 串行执行
            for index, item in enumerate(items):
                iter_result = await self._execute_single_item(
                    item, index, node_type,
                    item_port_name, result_port_name, node_config
                )
                
                if iter_result["success"]:
                    results.append(iter_result["result"])
                    success_count += 1
                else:
                    error_count += 1
                    errors.append({
                        "index": iter_result["index"],
                        "item": iter_result["item"],
                        "error": iter_result["error"]
                    })
                    
                    # 如果配置为遇错停止
                    if not continue_on_error:
                        logger.warning(
                            f"SimpleForEach 在迭代 {index} 处因错误停止",
                            extra=self.get_log_extra()
                        )
                        break
        
        logger.info(
            f"SimpleForEach 完成: {success_count} 成功, {error_count} 失败",
            extra=self.get_log_extra()
        )
        
        return {
            "results": results,
            "success_count": success_count,
            "error_count": error_count,
            "errors": errors
        }
