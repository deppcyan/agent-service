import axios from 'axios';
import type { NodeTypesResponse } from './nodeTypes';
import { transformNodeTypesResponse } from './nodeTypes';

const API_BASE_URL = 'http://192.168.0.238:8001/v1/workflow';
const API_KEY = import.meta.env.VITE_DIGEN_API_KEY || (() => {
  console.warn('VITE_DIGEN_API_KEY environment variable is not set. Please set it in your .env file.');
  return 'test-key';
})();

export interface NodePort {
  name: string;
  port_type: string;
  required: boolean;
  default_value?: any;
}

export interface NodeType {
  name: string;
  category: string;
  input_ports: Record<string, NodePort>;
  output_ports: Record<string, NodePort>;
}

export interface Connection {
  from_node: string;
  from_port: string;
  to_node: string;
  to_port: string;
}

export interface WorkflowData {
  nodes: Record<string, any>;
  connections: Connection[];
}

export interface ExecuteWorkflowRequest {
  workflow: WorkflowData;
}

export interface ExecuteWorkflowResponse {
  task_id: string;
  status: string;
}

export interface WorkflowStatusResponse {
  status: 'running' | 'completed' | 'error' | 'cancelled' | 'not_found';
  result: Record<string, any>;
  error?: string;
}

export const api = {

  async getNodeTypes(): Promise<NodeTypesResponse> {
    const response = await axios.get(`${API_BASE_URL}/nodes`, {
      headers: {
        'x-api-key': API_KEY
      }
    });
    return transformNodeTypesResponse(response.data);
  },

  async executeWorkflow(data: ExecuteWorkflowRequest): Promise<ExecuteWorkflowResponse> {
    const response = await axios.post(`${API_BASE_URL}/execute`, data, {
      headers: {
        'x-api-key': API_KEY
      }
    });
    return response.data;
  },

  async cancelWorkflow(taskId: string): Promise<{ task_id: string; status: string }> {
    const response = await axios.post(`${API_BASE_URL}/cancel/${taskId}`, null, {
      headers: {
        'x-api-key': API_KEY
      }
    });
    return response.data;
  },

  async getWorkflowStatus(taskId: string): Promise<WorkflowStatusResponse> {
    const response = await axios.get(`${API_BASE_URL}/status/${taskId}`, {
      headers: {
        'x-api-key': API_KEY
      }
    });
    return response.data;
  },
};
