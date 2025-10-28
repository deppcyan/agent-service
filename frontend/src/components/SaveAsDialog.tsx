import { useState } from 'react';

interface SaveAsDialogProps {
  isOpen: boolean;
  onClose: () => void;
  onSave: (name: string) => void;
  currentName?: string;
}

export default function SaveAsDialog({ isOpen, onClose, onSave, currentName }: SaveAsDialogProps) {
  const [name, setName] = useState(currentName || '');

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 w-96">
        <h2 className="text-lg font-semibold mb-4">Save Workflow As</h2>
        <input
          type="text"
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder="Enter workflow name"
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          autoFocus
        />
        <div className="flex justify-end gap-2 mt-4">
          <button
            onClick={onClose}
            className="px-4 py-2 text-gray-600 hover:text-gray-800"
          >
            Cancel
          </button>
          <button
            onClick={() => {
              if (name.trim()) {
                onSave(name.trim());
                onClose();
              }
            }}
            disabled={!name.trim()}
            className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 disabled:opacity-50"
          >
            Save
          </button>
        </div>
      </div>
    </div>
  );
}
