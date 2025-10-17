from typing import Dict, Any, List, Optional, Type, Union
from abc import ABC, abstractmethod
import asyncio
from .logger import logger
from app.services.base import AsyncServiceNode

class WorkflowStep(ABC):
    """Base class for workflow steps"""
    
    def __init__(self, name: str):
        self.name = name
    
    @abstractmethod
    async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the step"""
        pass

class ServiceStep(WorkflowStep):
    """Step that executes a service node"""
    
    def __init__(self, name: str, service: AsyncServiceNode, 
                 input_mapping: Dict[str, str], output_mapping: Dict[str, str],
                 callback_url: Optional[str] = None):
        super().__init__(name)
        self.service = service
        self.input_mapping = input_mapping
        self.output_mapping = output_mapping
        self.callback_url = callback_url
    
    async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the service"""
        # Map inputs from context
        input_data = {}
        for target, source in self.input_mapping.items():
            if source in context:
                input_data[target] = context[source]
            else:
                raise ValueError(f"Missing required input: {source}")
        
        # Execute service
        result = await self.service.generate(
            input_data,
            self.callback_url
        )
        
        # Map outputs to context
        output = {}
        for target, source in self.output_mapping.items():
            if source in result:
                output[target] = result[source]
        
        return output

class ParallelStep(WorkflowStep):
    """Step that executes multiple steps in parallel"""
    
    def __init__(self, name: str, steps: List[WorkflowStep]):
        super().__init__(name)
        self.steps = steps
    
    async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute all steps in parallel"""
        tasks = [step.execute(context.copy()) for step in self.steps]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Check for exceptions
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Step {self.steps[i].name} failed: {str(result)}", 
                           extra={"job_id": context["job_id"]})
                raise result
        
        # Merge results
        output = {}
        for result in results:
            output.update(result)
        return output

class ConditionalStep(WorkflowStep):
    """Step that executes based on a condition"""
    
    def __init__(self, name: str, condition: str, 
                 if_step: WorkflowStep, else_step: Optional[WorkflowStep] = None):
        super().__init__(name)
        self.condition = condition
        self.if_step = if_step
        self.else_step = else_step
    
    async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute step based on condition"""
        # Evaluate condition
        try:
            result = eval(self.condition, {"context": context})
            if result:
                return await self.if_step.execute(context)
            elif self.else_step:
                return await self.else_step.execute(context)
            return {}
        except Exception as e:
            logger.error(f"Condition evaluation failed: {str(e)}", 
                        extra={"job_id": context["job_id"]})
            raise

class Workflow:
    """Workflow executor"""
    
    def __init__(self, name: str, steps: List[WorkflowStep]):
        self.name = name
        self.steps = steps
    
    async def execute(self, initial_context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute workflow steps"""
        context = initial_context.copy()
        
        try:
            for step in self.steps:
                logger.info(f"Executing step: {step.name}", 
                          extra={"job_id": context["job_id"]})
                result = await step.execute(context)
                context.update(result)
            
            return context
            
        except Exception as e:
            logger.error(f"Workflow execution failed: {str(e)}", 
                        extra={"job_id": context["job_id"]})
            raise

class WorkflowBuilder:
    """Helper class for building workflows"""
    
    def __init__(self, name: str):
        self.name = name
        self.steps: List[WorkflowStep] = []
    
    def add_service(self, step: Union[ServiceStep, str], service: Optional[AsyncServiceNode] = None,
                   input_mapping: Optional[Dict[str, str]] = None,
                   output_mapping: Optional[Dict[str, str]] = None,
                   callback_url: Optional[str] = None) -> 'WorkflowBuilder':
        """Add a service step
        
        Can be called in two ways:
        1. add_service(service_step: ServiceStep)
        2. add_service(name: str, service: AsyncServiceNode, input_mapping: Dict, output_mapping: Dict, callback_url: Optional[str])
        """
        if isinstance(step, ServiceStep):
            self.steps.append(step)
        else:
            # Legacy way - construct ServiceStep from parameters
            service_step = ServiceStep(step, service, input_mapping, output_mapping, callback_url)
            self.steps.append(service_step)
        return self
    
    def add_parallel(self, name: str, steps: List[WorkflowStep]) -> 'WorkflowBuilder':
        """Add a parallel execution step"""
        step = ParallelStep(name, steps)
        self.steps.append(step)
        return self
    
    def add_conditional(self, name: str, condition: str,
                       if_step: WorkflowStep,
                       else_step: Optional[WorkflowStep] = None) -> 'WorkflowBuilder':
        """Add a conditional step"""
        step = ConditionalStep(name, condition, if_step, else_step)
        self.steps.append(step)
        return self
    
    def build(self) -> Workflow:
        """Build the workflow"""
        return Workflow(self.name, self.steps)
