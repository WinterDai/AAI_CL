import React, { useState, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { oneLight } from 'react-syntax-highlighter/dist/esm/styles/prism';
import Button from '../../common/Button';
import Card from '../../common/Card';
import { useGenerationStore } from '../../../store/generationStore';

export default function Step8FinalReview({ itemId }) {
  const { 
    module,
    generatedCode,
    generatedReadme,
    setGeneratedCode,
    setGeneratedReadme,
    setCurrentStep,
    project,
    getStep1State,
    // Step8 persistent state
    step8IsProcessing,
    setStep8IsProcessing
  } = useGenerationStore();
  
  // Get step1State using the getter (returns correct values based on lock status)
  const step1State = getStep1State();
  
  const [viewMode, setViewMode] = useState('code'); // 'code' or 'readme'
  const [codeViewMode, setCodeViewMode] = useState('rendered'); // 'rendered' or 'raw'
  const [editMode, setEditMode] = useState(false);
  const [editTarget, setEditTarget] = useState('code'); // 'code' or 'readme'
  const [editedCode, setEditedCode] = useState(generatedCode || '');
  const [editedReadme, setEditedReadme] = useState(generatedReadme || '');
  const [message, setMessage] = useState('');
  
  // Backup state for Reset functionality
  const [backupCode, setBackupCode] = useState(null);
  const [backupReadme, setBackupReadme] = useState(null);

  // Get effective values
  const effectiveModule = project?.locked ? project.module : (step1State?.selectedModule || module);
  const effectiveItemId = project?.locked ? project.itemId : (step1State?.selectedItem || itemId);

  // Initialize backup on first load
  useEffect(() => {
    if (generatedCode && backupCode === null) {
      setBackupCode(generatedCode);
    }
    if (generatedReadme && backupReadme === null) {
      setBackupReadme(generatedReadme);
    }
  }, [generatedCode, generatedReadme, backupCode, backupReadme]);

  // Sync edited content when store changes
  useEffect(() => {
    if (!editMode) {
      setEditedCode(generatedCode || '');
      setEditedReadme(generatedReadme || '');
    }
  }, [generatedCode, generatedReadme, editMode]);

  // Handle Test - go back to Step7
  const handleTest = () => {
    setCurrentStep(7);
  };

  // Handle Modify - enter edit mode
  const handleModify = (target = 'code') => {
    setEditTarget(target);
    setEditMode(true);
    if (target === 'code') {
      setEditedCode(generatedCode || '');
    } else {
      setEditedReadme(generatedReadme || '');
    }
  };

  // Handle Save - save changes locally (no API call)
  const handleSave = () => {
    if (editTarget === 'code') {
      setGeneratedCode(editedCode);
      setMessage('Code saved successfully');
    } else {
      setGeneratedReadme(editedReadme);
      setMessage('README saved successfully');
    }
    setEditMode(false);
    // Clear message after 3 seconds
    setTimeout(() => setMessage(''), 3000);
  };

  // Handle Cancel - discard changes
  const handleCancelEdit = () => {
    setEditMode(false);
    setEditedCode(generatedCode || '');
    setEditedReadme(generatedReadme || '');
  };

  // Handle Reset - restore current view from backup (Code or README based on viewMode)
  const handleReset = () => {
    const isCodeView = viewMode === 'code';
    const targetBackup = isCodeView ? backupCode : backupReadme;
    const targetName = isCodeView ? 'Code' : 'README';
    
    if (targetBackup !== null) {
      const confirmed = window.confirm(`Reset ${targetName} to its backup version?`);
      if (confirmed) {
        if (isCodeView) {
          setGeneratedCode(backupCode);
          setEditedCode(backupCode);
        } else {
          setGeneratedReadme(backupReadme);
          setEditedReadme(backupReadme);
        }
        setMessage(`${targetName} restored to backup version`);
        setTimeout(() => setMessage(''), 3000);
      }
    } else {
      setMessage(`No ${targetName} backup available`);
      setTimeout(() => setMessage(''), 3000);
    }
  };

  if (!generatedCode) {
    return (
      <Card>
        <div className="text-center py-8">
          <p className="text-gray-500 mb-4">Please complete Steps 1-7 first</p>
          <Button onClick={() => setCurrentStep(7)}>
            Go to Step 7
          </Button>
        </div>
      </Card>
    );
  }

  return (
    <div className="p-4 space-y-3">
      <Card>
        <div className="mb-3">
          <h2 className="text-base font-semibold mb-1">Step 8: Final Review</h2>
          <p className="text-xs text-gray-600">
            Review and modify your checker code and README
          </p>
        </div>

        {/* Message Display */}
        {message && (
          <div className="mb-3 p-2 bg-blue-50 border border-blue-200 rounded-lg text-xs">
            {message}
          </div>
        )}

        {/* Action Buttons - Only Test, Modify, Reset */}
        {!editMode ? (
          <div className="flex flex-wrap gap-1.5 mb-4">
            <button
              onClick={handleTest}
              className="px-2 py-1 border border-gray-300 rounded text-xs hover:bg-gray-100"
              title="Back to Step7 testing"
            >
              🧪 Test
            </button>
            <button
              onClick={() => handleModify(viewMode === 'readme' ? 'readme' : 'code')}
              className="px-2 py-1 border border-gray-300 rounded text-xs hover:bg-gray-100"
              title={`Edit ${viewMode === 'readme' ? 'README' : 'Code'}`}
            >
              ✏️ Modify {viewMode === 'readme' ? 'README' : 'Code'}
            </button>
            <button
              onClick={handleReset}
              className="px-2 py-1 border border-gray-300 rounded text-xs hover:bg-gray-100"
              title={`Restore ${viewMode === 'readme' ? 'README' : 'Code'} to backup`}
            >
              🔄 Reset {viewMode === 'readme' ? 'README' : 'Code'}
            </button>
          </div>
        ) : (
          <div className="flex gap-1.5 mb-3">
            <Button
              onClick={handleSave}
              className="bg-green-600 hover:bg-green-700"
              size="xs"
            >
              💾 Save {editTarget === 'readme' ? 'README' : 'Code'}
            </Button>
            <Button
              onClick={handleCancelEdit}
              variant="secondary"
              size="xs"
            >
              ❌ Cancel
            </Button>
            {/* Switch edit target */}
            <Button
              onClick={() => {
                const newTarget = editTarget === 'code' ? 'readme' : 'code';
                setEditTarget(newTarget);
                if (newTarget === 'code') {
                  setEditedCode(generatedCode || '');
                } else {
                  setEditedReadme(generatedReadme || '');
                }
              }}
              variant="secondary"
              size="xs"
            >
              🔀 Switch to {editTarget === 'code' ? 'README' : 'Code'}
            </Button>
          </div>
        )}

        {/* View Mode Tabs: Code / README */}
        {!editMode && (
          <div className="flex gap-1.5 mb-3 border-b border-gray-200 pb-2">
            <Button
              onClick={() => setViewMode('code')}
              variant={viewMode === 'code' ? 'primary' : 'secondary'}
              size="xs"
            >
              📄 Code
            </Button>
            <Button
              onClick={() => setViewMode('readme')}
              variant={viewMode === 'readme' ? 'primary' : 'secondary'}
              size="xs"
            >
              📖 README
            </Button>
          </div>
        )}

        {/* Content Display/Edit */}
        {!editMode ? (
          <>
            {viewMode === 'code' ? (
              <>
                <div className="flex gap-1.5 mb-3">
                  <Button
                    onClick={() => setCodeViewMode('rendered')}
                    variant={codeViewMode === 'rendered' ? 'primary' : 'secondary'}
                    size="xs"
                  >
                    🎨 Syntax Highlighted
                  </Button>
                  <Button
                    onClick={() => setCodeViewMode('raw')}
                    variant={codeViewMode === 'raw' ? 'primary' : 'secondary'}
                    size="xs"
                  >
                    📝 Raw Code
                  </Button>
                </div>

                {codeViewMode === 'rendered' ? (
                  <div className="border border-gray-200 rounded-lg overflow-hidden">
                    <SyntaxHighlighter
                      language="python"
                      style={oneLight}
                      customStyle={{
                        margin: 0,
                        maxHeight: '480px',
                        fontSize: '11px',
                        backgroundColor: '#fafafa'
                      }}
                      showLineNumbers
                    >
                      {generatedCode}
                    </SyntaxHighlighter>
                  </div>
                ) : (
                  <div className="bg-gray-50 border border-gray-200 text-gray-800 p-4 rounded-lg overflow-auto max-h-[480px]">
                    <pre className="text-xs whitespace-pre-wrap font-mono">
                      {generatedCode}
                    </pre>
                  </div>
                )}
              </>
            ) : (
              /* README View - Same style as Step3 */
              <div className="border border-gray-200 rounded-lg overflow-auto max-h-[520px] bg-white p-4">
                {generatedReadme ? (
                  <div className="prose prose-sm max-w-none">
                    <ReactMarkdown
                      remarkPlugins={[remarkGfm]}
                      components={{
                        code({node, inline, className, children, ...props}) {
                          const match = /language-(\w+)/.exec(className || '')
                          return !inline && match ? (
                            <SyntaxHighlighter
                              style={{
                                'pre[class*="language-"]': {
                                  background: '#f8fafc',
                                  border: '1px solid #e2e8f0',
                                  borderRadius: '0.375rem',
                                  padding: '0.5rem',
                                  fontSize: '0.75rem',
                                  lineHeight: '1.4',
                                  overflow: 'auto',
                                },
                                'code[class*="language-"]': {
                                  color: '#334155',
                                  fontFamily: 'inherit',
                                },
                                'comment': { color: '#64748b' },
                                'punctuation': { color: '#64748b' },
                                'property': { color: '#0369a1' },
                                'string': { color: '#059669' },
                                'keyword': { color: '#7c3aed' },
                                'function': { color: '#0284c7' },
                                'number': { color: '#d97706' },
                                'operator': { color: '#475569' },
                                'class-name': { color: '#0891b2' },
                                'tag': { color: '#dc2626' },
                                'attr-name': { color: '#0369a1' },
                                'attr-value': { color: '#059669' },
                              }}
                              language={match[1]}
                              PreTag="div"
                              customStyle={{ fontFamily: 'inherit' }}
                              {...props}
                            >
                              {String(children).replace(/\n$/, '')}
                            </SyntaxHighlighter>
                          ) : (
                            <code className="px-1 py-0.5 bg-gray-100 text-gray-700 rounded text-xs" {...props}>
                              {children}
                            </code>
                          )
                        },
                        h1: ({children}) => <h1 className="text-base font-bold mt-4 mb-3 text-gray-900">{children}</h1>,
                        h2: ({children}) => <h2 className="text-sm font-semibold mt-3 mb-2 text-gray-800 border-b pb-1">{children}</h2>,
                        h3: ({children}) => <h3 className="text-xs font-semibold mt-2 mb-1 text-gray-700">{children}</h3>,
                        p: ({children}) => <p className="mb-2 text-xs text-gray-700 leading-relaxed">{children}</p>,
                        ul: ({children}) => <ul className="list-disc pl-5 mb-2 space-y-0.5 text-xs">{children}</ul>,
                        ol: ({children}) => <ol className="list-decimal pl-5 mb-2 space-y-0.5 text-xs">{children}</ol>,
                        li: ({children}) => <li className="text-xs text-gray-700">{children}</li>,
                        strong: ({children}) => <strong className="font-semibold text-gray-900">{children}</strong>,
                        blockquote: ({children}) => <blockquote className="border-l-3 border-gray-300 pl-3 italic text-xs text-gray-600 my-2">{children}</blockquote>,
                        table: ({children}) => <div className="overflow-x-auto my-2"><table className="min-w-full border border-gray-300 text-xs">{children}</table></div>,
                        th: ({children}) => <th className="border border-gray-300 px-2 py-1 bg-gray-100 font-semibold text-left text-xs">{children}</th>,
                        td: ({children}) => <td className="border border-gray-300 px-2 py-1 text-xs">{children}</td>,
                      }}
                    >
                      {generatedReadme}
                    </ReactMarkdown>
                  </div>
                ) : (
                  <div className="text-center text-gray-500 text-sm py-8">
                    No README available. Please complete Step 3 first.
                  </div>
                )}
              </div>
            )}
          </>
        ) : (
          /* Edit Mode */
          <div>
            <div className="text-xs text-gray-600 mb-2">
              Editing: <span className="font-semibold">{editTarget === 'readme' ? 'README' : 'Code'}</span>
            </div>
            <textarea
              value={editTarget === 'code' ? editedCode : editedReadme}
              onChange={(e) => {
                if (editTarget === 'code') {
                  setEditedCode(e.target.value);
                } else {
                  setEditedReadme(e.target.value);
                }
              }}
              className="w-full h-[480px] font-mono text-xs p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-gray-50 text-gray-800"
              style={{ resize: 'vertical' }}
            />
            <p className="text-xs text-gray-500 mt-1">
              {(editTarget === 'code' ? editedCode : editedReadme).length} characters • 
              {(editTarget === 'code' ? editedCode : editedReadme).split('\n').length} lines
            </p>
          </div>
        )}
      </Card>
    </div>
  );
}
