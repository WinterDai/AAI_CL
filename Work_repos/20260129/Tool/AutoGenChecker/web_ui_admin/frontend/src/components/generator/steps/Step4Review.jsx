import React, { useState } from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter'
import Button from '../../common/Button'
import Card from '../../common/Card'
import { useGenerationStore } from '../../../store/generationStore'
import { useSettingsStore } from '../../../store/settingsStore'
import apiClient from '../../../api/client'

export const Step4Review = () => {
  const { 
    generatedReadme, 
    setGeneratedReadme,
    setCurrentStep,
    project,
    getStep1State
  } = useGenerationStore();
  
  // Get step1State using the getter (returns correct values based on lock status)
  const step1State = getStep1State();
  
  // Get effective module and item_id from locked project
  const effectiveModule = project?.locked ? project.module : step1State?.selectedModule;
  const effectiveItemId = project?.locked ? project.itemId : step1State?.selectedItem;
  
  const settings = useSettingsStore((s) => s.settings);
  
  const [isEditing, setIsEditing] = useState(false);
  const [isAiEditing, setIsAiEditing] = useState(false);
  const [editedReadme, setEditedReadme] = useState(generatedReadme);
  const [aiPrompt, setAiPrompt] = useState('');
  const [viewMode, setViewMode] = useState('rendered'); // 'rendered' or 'raw'
  const [isLoading, setIsLoading] = useState(false);

  const handleAction = async (action, extraData = {}) => {
    setIsLoading(true);
    try {
      const response = await apiClient.post('/api/step4/review-readme', {
        action: action,
        module: effectiveModule || '',
        item_id: effectiveItemId || '',
        readme: generatedReadme,
        edited_readme: action === 'edit' ? editedReadme : null,
        ai_prompt: action === 'ai_edit' ? aiPrompt : null,
        llm_provider: settings?.llmProvider || 'jedai',
        llm_model: settings?.llmModel || 'claude-sonnet-4-5',
        ...extraData
      });

      if (response.data.status === 'success' || response.data.status === 'warning') {
        if (action === 'keep') {
          setCurrentStep(5);
        } else if (action === 'edit') {
          setGeneratedReadme(editedReadme);
          setIsEditing(false);
          setCurrentStep(5);
        } else if (action === 'ai_edit') {
          // AI modified the README, update and stay on Step 4 for review
          setGeneratedReadme(response.data.readme);
          setIsAiEditing(false);
          setAiPrompt('');
          alert('✅ README modified by AI. Please review the changes.');
        } else if (action === 'load') {
          if (response.data.readme) {
            setGeneratedReadme(response.data.readme);
            alert('✅ README reloaded from file');
          }
        } else if (action === 'back' || action === 'reset') {
          if (response.data.readme) {
            setGeneratedReadme(response.data.readme);
          }
          setCurrentStep(response.data.next_step || 3);
        }
      }
    } catch (error) {
      console.error(`Action ${action} failed:`, error);
      alert(`Action failed: ${error.message}`);
    } finally {
      setIsLoading(false);
    }
  };

  const handleEdit = () => {
    setIsEditing(true);
    setIsAiEditing(false);
    setEditedReadme(generatedReadme);
  };

  const handleAiEdit = () => {
    setIsAiEditing(true);
    setIsEditing(false);
    setAiPrompt('');
  };

  const handleCancelEdit = () => {
    setIsEditing(false);
    setIsAiEditing(false);
    setEditedReadme(generatedReadme);
    setAiPrompt('');
  };

  const handleSaveEdit = async () => {
    await handleAction('edit');
  };

  const handleSubmitAiEdit = async () => {
    if (!aiPrompt.trim()) {
      alert('Please describe what you want to change');
      return;
    }
    await handleAction('ai_edit');
  };

  if (!generatedReadme) {
    return (
      <Card>
        <div className="text-center py-8">
          <p className="text-gray-500 mb-4">No README generated yet</p>
          <Button onClick={() => setCurrentStep(3)}>
            Go to Step 3 to Generate README
          </Button>
        </div>
      </Card>
    );
  }

  return (
    <div className="p-4 space-y-4">
      {/* Header */}
      <div>
        <h1 className="text-base font-semibold text-gray-900">
          Step 4: Review & Refine README
        </h1>
        <p className="mt-1 text-xs text-gray-600">
          Review the generated README and take action if needed
        </p>
      </div>

      {/* Action Guide */}
      <Card>
        <div className="space-y-2">
          <h3 className="text-xs font-semibold text-gray-700 uppercase tracking-wide">Available Actions</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-x-4 gap-y-1 text-xs">
            <div><span className="font-medium text-gray-900">Keep (K):</span> <span className="text-gray-600">Accept and proceed to code generation</span></div>
            <div><span className="font-medium text-gray-900">AI-Edit (A):</span> <span className="text-gray-600">Modify README using AI</span></div>
            <div><span className="font-medium text-gray-900">Edit (E):</span> <span className="text-gray-600">Manually edit the README</span></div>
            <div><span className="font-medium text-gray-900">Load (L):</span> <span className="text-gray-600">Reload from file</span></div>
            <div><span className="font-medium text-gray-900">Back (B):</span> <span className="text-gray-600">Return to Step 3</span></div>
            <div><span className="font-medium text-gray-900">Reset (R):</span> <span className="text-gray-600">Restore TODO template</span></div>
          </div>
        </div>
      </Card>

      {/* Action Buttons & Content */}
      <Card>

        {/* Action Buttons - Normal Mode */}
        {!isEditing && !isAiEditing && (
          <div className="flex flex-wrap gap-1.5 mb-4">
            <Button
              onClick={() => handleAction('keep')}
              disabled={isLoading}
              size="xs"
              className="bg-green-600 hover:bg-green-700 text-white"
            >
              Keep (K)
            </Button>
            <Button
              onClick={handleAiEdit}
              disabled={isLoading}
              size="xs"
              className="bg-purple-600 hover:bg-purple-700 text-white"
            >
              AI-Edit (A)
            </Button>
            <Button
              onClick={handleEdit}
              disabled={isLoading}
              size="xs"
            >
              Edit (E)
            </Button>
            <Button
              onClick={() => handleAction('load')}
              disabled={isLoading}
              size="xs"
              variant="secondary"
            >
              Load (L)
            </Button>
            <Button
              onClick={() => handleAction('back')}
              disabled={isLoading}
              size="xs"
              variant="secondary"
            >
              Back (B)
            </Button>
            <Button
              onClick={() => handleAction('reset')}
              disabled={isLoading}
              size="xs"
              className="bg-orange-600 hover:bg-orange-700 text-white"
            >
              Reset (R)
            </Button>
          </div>
        )}

        {/* AI Edit Mode */}
        {isAiEditing && (
          <div className="mb-4 p-3 bg-purple-50 border border-purple-200 rounded-lg">
            <h3 className="font-semibold text-purple-900 mb-2 text-sm">AI-Assisted README Edit</h3>
            <p className="text-xs text-gray-700 mb-1">
              Describe what you want to change:
            </p>
            <ul className="list-disc list-inside text-xs text-gray-600 mb-3 space-y-0.5">
              <li>Change found_desc to 'Clean max transition checks'</li>
              <li>Add more waive_items examples for Type 3</li>
              <li>Fix the pattern_items to use actual view names</li>
            </ul>
            <textarea
              value={aiPrompt}
              onChange={(e) => setAiPrompt(e.target.value)}
              placeholder="Enter your modification request..."
              className="w-full h-20 p-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent text-xs"
            />
            <div className="flex gap-1.5 mt-3">
              <Button
                onClick={handleSubmitAiEdit}
                disabled={isLoading || !aiPrompt.trim()}
                size="xs"
                className="bg-purple-600 hover:bg-purple-700 text-white"
              >
                {isLoading ? 'Processing...' : 'Apply Changes'}
              </Button>
              <Button
                onClick={handleCancelEdit}
                disabled={isLoading}
                size="xs"
                variant="secondary"
              >
                Cancel
              </Button>
            </div>
          </div>
        )}

        {/* Manual Edit Mode */}
        {isEditing && (
          <div className="flex gap-1.5 mb-4">
            <Button
              onClick={handleSaveEdit}
              disabled={isLoading}
              size="xs"
              className="bg-green-600 hover:bg-green-700 text-white"
            >
              Save and Continue
            </Button>
            <Button
              onClick={handleCancelEdit}
              disabled={isLoading}
              size="xs"
              variant="secondary"
            >
              Cancel
            </Button>
          </div>
        )}

        {/* View Mode Toggle - matches Step3 style */}
        {!isEditing && !isAiEditing && (
          <div className="flex items-center space-x-1.5 bg-gray-100 rounded-lg p-1 mb-3">
            <button
              onClick={() => setViewMode('rendered')}
              className={`px-2 py-1 text-xs rounded transition-colors ${
                viewMode === 'rendered'
                  ? 'bg-white text-gray-900 shadow-sm'
                  : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              📄 Rendered
            </button>
            <button
              onClick={() => setViewMode('raw')}
              className={`px-2 py-1 text-xs rounded transition-colors ${
                viewMode === 'raw'
                  ? 'bg-white text-gray-900 shadow-sm'
                  : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              📝 Raw
            </button>
          </div>
        )}

        {/* README Content */}
        {isEditing ? (
          <div>
            <textarea
              value={editedReadme}
              onChange={(e) => setEditedReadme(e.target.value)}
              className="w-full h-[400px] font-mono text-xs text-gray-900 border border-gray-300 rounded-lg p-3 focus:outline-none focus:ring-2 focus:ring-primary/50 resize-none"
              placeholder="Edit README content..."
            />
          </div>
        ) : viewMode === 'rendered' ? (
          <div className="bg-white border border-gray-200 rounded-lg p-4 max-h-[480px] overflow-auto custom-scrollbar">
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
          </div>
        ) : (
          <div className="bg-white border border-gray-200 rounded-lg p-4 max-h-[480px] overflow-auto custom-scrollbar">
            <pre className="text-xs text-gray-900 whitespace-pre-wrap font-mono">
              {generatedReadme}
            </pre>
          </div>
        )}
      </Card>
    </div>
  )
}

export default Step4Review
