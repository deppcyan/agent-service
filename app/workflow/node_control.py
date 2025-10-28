from typing import Dict, Any, List, Optional, TypeVar, Generic, Union
from dataclasses import dataclass
from abc import ABC, abstractmethod
from app.workflow.base import WorkflowNode
from app.utils.logger import logger

T = TypeVar('T')  # 输入项的类型
R = TypeVar('R')  # 结果项的类型

@dataclass
class IterationResult(Generic[T, R]):
    """迭代处理的结果"""
    input_item: T
    output: R
    success: bool
    error: Optional[str] = None

class IterativeNode(WorkflowNode, ABC):
    """循环处理节点
    
    用于对列表中的每个项目进行处理。支持：
    - 并行/顺序处理
    - 错误处理和恢复
    - 结果统计
    
    子类只需要实现 process_item 方法来处理单个项目即可。
    """
    
    category = "control"
    
    def __init__(self, node_id: Optional[str] = None):
        super().__init__(node_id)
        # 基础输入端口
        self.add_input_port("items", "array", True)  # 要处理的项目列表
        self.add_input_port("parallel", "boolean", False, False)  # 是否并行处理
        self.add_input_port("continue_on_error", "boolean", False, True)  # 出错时是否继续
        
        # 基础输出端口
        self.add_output_port("results", "array")  # 处理结果列表
        self.add_output_port("success_count", "number")  # 成功处理的数量
        self.add_output_port("error_count", "number")  # 失败的数量
        self.add_output_port("errors", "array")  # 错误详情列表
    
    @abstractmethod
    async def process_item(self, item: Any) -> Any:
        """处理单个项目的抽象方法，子类必须实现
        
        Args:
            item: 要处理的单个项目
            
        Returns:
            处理结果
            
        Raises:
            NotImplementedError: 子类必须实现此方法
        """
        raise NotImplementedError("Subclasses must implement process_item")
    
    async def _safe_process_item(self, item: Any) -> IterationResult:
        """安全地处理单个项目，包含错误处理"""
        try:
            output = await self.process_item(item)
            return IterationResult(
                input_item=item,
                output=output,
                success=True
            )
        except Exception as e:
            logger.error(f"Error processing item: {str(e)}")
            return IterationResult(
                input_item=item,
                output=None,
                success=False,
                error=str(e)
            )
    
    async def process(self) -> Dict[str, Any]:
        """处理整个列表"""
        if not self.validate_inputs():
            raise ValueError("Required inputs missing")
        
        items = self.input_values["items"]
        parallel = self.input_values.get("parallel", False)
        continue_on_error = self.input_values.get("continue_on_error", True)
        
        results: List[IterationResult] = []
        success_count = 0
        error_count = 0
        errors = []
        
        if parallel:
            # 并行处理
            import asyncio
            tasks = [self._safe_process_item(item) for item in items]
            results = await asyncio.gather(*tasks)
        else:
            # 顺序处理
            for item in items:
                result = await self._safe_process_item(item)
                results.append(result)
                
                # 如果有错误且不继续，则停止处理
                if not result.success and not continue_on_error:
                    break
        
        # 统计结果
        for result in results:
            if result.success:
                success_count += 1
            else:
                error_count += 1
                errors.append({
                    "input": result.input_item,
                    "error": result.error
                })
        
        return {
            "results": [r.output for r in results if r.success],
            "success_count": success_count,
            "error_count": error_count,
            "errors": errors
        }