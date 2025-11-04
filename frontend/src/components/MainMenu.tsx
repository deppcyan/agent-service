import { useState, useRef, useEffect } from 'react';
import { ChevronDownIcon } from '@heroicons/react/24/outline';

interface MainMenuProps {
  onNew: () => void;
  onImport: () => void;
  onSave: () => void;
  onSaveAs: () => void;
  onExport: () => void;
  canSave: boolean;
  currentWorkflowName?: string;
}

export default function MainMenu({
  onNew,
  onImport,
  onSave,
  onSaveAs,
  onExport,
  canSave
}: MainMenuProps) {
  const [isOpen, setIsOpen] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);

  // Close menu when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, []);

  const handleMenuItemClick = (action: () => void) => {
    action();
    setIsOpen(false);
  };

  return (
    <div className="relative" ref={menuRef}>
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-2 px-4 py-2 bg-gray-700 text-gray-200 rounded hover:bg-gray-600 transition-colors"
      >
        <span>File</span>
        <ChevronDownIcon className="w-4 h-4" />
      </button>

      {isOpen && (
        <div className="absolute top-full left-0 mt-1 bg-gray-800 rounded-lg shadow-lg py-1 z-50 min-w-[160px] border border-gray-700">
          <button
            onClick={() => handleMenuItemClick(onNew)}
            className="w-full px-4 py-2 text-left text-gray-300 hover:bg-gray-700 hover:text-white flex items-center gap-2"
          >
            <span>New</span>
            <span className="text-xs text-gray-500 ml-auto">Ctrl+N</span>
          </button>
          
          <div className="border-t border-gray-700 my-1"></div>
          
          <button
            onClick={() => handleMenuItemClick(onImport)}
            className="w-full px-4 py-2 text-left text-gray-300 hover:bg-gray-700 hover:text-white flex items-center gap-2"
          >
            <span>Import</span>
            <span className="text-xs text-gray-500 ml-auto">Ctrl+O</span>
          </button>
          
          <div className="border-t border-gray-700 my-1"></div>
          
          <button
            onClick={() => handleMenuItemClick(onSave)}
            disabled={!canSave}
            className={`w-full px-4 py-2 text-left flex items-center gap-2 ${
              canSave 
                ? 'text-gray-300 hover:bg-gray-700 hover:text-white' 
                : 'text-gray-500 cursor-not-allowed'
            }`}
          >
            <span>Save</span>
            <span className="text-xs text-gray-500 ml-auto">Ctrl+S</span>
          </button>
          
          <button
            onClick={() => handleMenuItemClick(onSaveAs)}
            className="w-full px-4 py-2 text-left text-gray-300 hover:bg-gray-700 hover:text-white flex items-center gap-2"
          >
            <span>Save As...</span>
            <span className="text-xs text-gray-500 ml-auto">Ctrl+Shift+S</span>
          </button>
          
          <div className="border-t border-gray-700 my-1"></div>
          
          <button
            onClick={() => handleMenuItemClick(onExport)}
            className="w-full px-4 py-2 text-left text-gray-300 hover:bg-gray-700 hover:text-white flex items-center gap-2"
          >
            <span>Export</span>
            <span className="text-xs text-gray-500 ml-auto">Ctrl+E</span>
          </button>
        </div>
      )}
    </div>
  );
}
