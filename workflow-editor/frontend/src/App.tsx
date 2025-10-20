import { useEffect, useState } from 'react';
import { api } from './services/api';
import WorkflowEditor from './components/WorkflowEditor';

function App() {
  const [workflows, setWorkflows] = useState<string[]>([]);
  const [selectedWorkflow, setSelectedWorkflow] = useState<string | null>(null);

  useEffect(() => {
    const loadWorkflows = async () => {
      try {
        const { workflows } = await api.listWorkflows();
        setWorkflows(workflows);
        if (workflows.length > 0) {
          setSelectedWorkflow(workflows[0]);
        }
      } catch (error) {
        console.error('Failed to load workflows:', error);
      }
    };

    loadWorkflows();
  }, []);

  if (!selectedWorkflow) {
    return <div>Loading...</div>;
  }

  return (
    <div className="h-screen flex flex-col">
      <div className="bg-gray-800 text-white p-4">
        <select
          value={selectedWorkflow}
          onChange={(e) => setSelectedWorkflow(e.target.value)}
          className="bg-gray-700 text-white px-4 py-2 rounded"
        >
          {workflows.map((workflow) => (
            <option key={workflow} value={workflow}>
              {workflow}
            </option>
          ))}
        </select>
      </div>
      <div className="flex-1">
        <WorkflowEditor filename={selectedWorkflow} />
      </div>
    </div>
  );
}

export default App;