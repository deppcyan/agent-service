import axios from 'axios';

const API_BASE_URL = 'http://192.168.0.238:8080/api';

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

export const api = {
  async listWorkflows() {
    const response = await axios.get(`${API_BASE_URL}/workflows`);
    return response.data;
  },

  async getWorkflow(filename: string) {
    const response = await axios.get(`${API_BASE_URL}/workflows/${filename}`);
    return response.data;
  },

  async updateWorkflow(filename: string, data: WorkflowData) {
    const response = await axios.put(`${API_BASE_URL}/workflows/${filename}`, data);
    return response.data;
  },
};
