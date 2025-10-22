import type { NodeType } from './api';

export interface NodeTypesResponse {
  nodes: NodeType[];
  categories: Record<string, string[]>;
}

export const transformNodeTypesResponse = (data: any): NodeTypesResponse => {
  const nodes = data.nodes.map((node: any) => ({
    name: node.name,
    category: node.category,
    input_ports: node.input_ports,
    output_ports: node.output_ports,
  }));

  return {
    nodes,
    categories: data.categories,
  };
};
