import { useState } from 'react'
import Button from '@/components/common/Button'
import StatusBadge from '@/components/common/StatusBadge'

export default function HistoryDetail({ item, onClose }) {
  const [activeTab, setActiveTab] = useState('overview')

  const tabs = [
    { id: 'overview', label: 'Overview' },
    { id: 'logs', label: 'Logs' },
    { id: 'code', label: 'Code' },
    { id: 'readme', label: 'README' },
    { id: 'yaml', label: 'YAML' },
    { id: 'tests', label: 'Tests' }
  ]

  const mockLogs = `[12:32:01] Starting generation for IMP-10-0-0-13
[12:32:02] Loading configuration...
[12:32:03] Configuration loaded successfully
[12:32:04] Analyzing input files...
[12:32:07] File analysis complete
[12:32:08] Generating README...
[12:32:12] README generation complete
[12:32:13] Implementing checker code...
[12:32:18] Code generation complete
[12:32:19] Running self-check...
[12:32:22] Self-check passed
[12:32:23] Generating tests...
[12:32:27] Tests generated successfully
[12:32:28] Running tests...
[12:32:32] All tests passed (9/9)
[12:32:33] Creating package...
[12:32:35] Package created successfully`

  const mockCode = `"""
IMP-10-0-0-13: STA DCD Timing Violations Check
"""

import re
from pathlib import Path

class TimingChecker:
    def __init__(self, timing_rpt):
        self.timing_rpt = Path(timing_rpt)
        self.violations = []
        
    def parse_timing_report(self):
        with open(self.timing_rpt, 'r') as f:
            content = f.read()
        # ... parsing logic
        return violations`

  return (
    <div className="fixed right-0 top-16 bottom-0 w-96 bg-white border-l border-gray-200 shadow-xl overflow-hidden flex flex-col">
      {/* Header */}
      <div className="p-6 border-b border-gray-200">
        <div className="flex items-start justify-between mb-4">
          <div className="flex-1">
            <h2 className="text-lg font-semibold text-gray-900">{item.itemId}</h2>
            <p className="text-sm text-gray-600 mt-1">{item.description}</p>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 ml-4"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
        <StatusBadge status={item.status} />
      </div>

      {/* Tabs */}
      <div className="border-b border-gray-200 px-6">
        <div className="flex space-x-6 overflow-x-auto">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`py-3 text-sm font-medium border-b-2 whitespace-nowrap ${
                activeTab === tab.id
                  ? 'border-primary text-primary'
                  : 'border-transparent text-gray-600 hover:text-gray-900'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-auto custom-scrollbar p-6">
        {activeTab === 'overview' && (
          <div className="space-y-6">
            <div>
              <h3 className="text-sm font-semibold text-gray-900 mb-3">Basic Information</h3>
              <div className="space-y-3 text-sm">
                <div className="flex justify-between">
                  <span className="text-gray-600">Module:</span>
                  <span className="text-gray-900 font-medium">{item.module}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Created:</span>
                  <span className="text-gray-900">{item.createdAt}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Duration:</span>
                  <span className="text-gray-900">{item.duration}</span>
                </div>
                {item.filesGenerated && (
                  <div className="flex justify-between">
                    <span className="text-gray-600">Files Generated:</span>
                    <span className="text-gray-900">{item.filesGenerated}</span>
                  </div>
                )}
              </div>
            </div>

            {item.testsPassed && (
              <div>
                <h3 className="text-sm font-semibold text-gray-900 mb-3">Test Results</h3>
                <div className="space-y-3 text-sm">
                  <div className="flex justify-between">
                    <span className="text-gray-600">Tests Passed:</span>
                    <span className="text-success font-medium">{item.testsPassed}/9</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Coverage:</span>
                    <span className="text-primary font-medium">{item.coverage}%</span>
                  </div>
                </div>
              </div>
            )}

            {item.error && (
              <div className="p-3 bg-error/10 border border-error/30 rounded-lg">
                <div className="text-sm font-medium text-error mb-1">Error</div>
                <div className="text-sm text-gray-700">{item.error}</div>
              </div>
            )}

            <div className="pt-4 space-y-2">
              <Button className="w-full" size="sm">
                Download Package
              </Button>
              <Button variant="secondary" className="w-full" size="sm">
                Clone & Edit
              </Button>
              {item.status === 'IN_PROGRESS' && (
                <Button variant="secondary" className="w-full" size="sm">
                  Resume Generation
                </Button>
              )}
            </div>
          </div>
        )}

        {activeTab === 'logs' && (
          <div>
            <div className="bg-gray-900 rounded-lg p-4 overflow-auto">
              <pre className="text-xs text-gray-100 font-mono whitespace-pre-wrap">
                {mockLogs}
              </pre>
            </div>
            <div className="mt-4">
              <Button variant="secondary" size="sm" className="w-full">
                Download Logs
              </Button>
            </div>
          </div>
        )}

        {activeTab === 'code' && (
          <div>
            <div className="bg-gray-900 rounded-lg p-4 overflow-auto max-h-[500px]">
              <pre className="text-xs text-gray-100 font-mono whitespace-pre-wrap">
                {mockCode}
              </pre>
            </div>
            <div className="mt-4 flex space-x-2">
              <Button variant="secondary" size="sm" className="flex-1">
                Copy Code
              </Button>
              <Button variant="secondary" size="sm" className="flex-1">
                Download
              </Button>
            </div>
          </div>
        )}

        {activeTab === 'readme' && (
          <div>
            <div className="bg-gray-50 rounded-lg p-4 overflow-auto max-h-[500px]">
              <div className="prose prose-sm max-w-none">
                <h1>IMP-10-0-0-13: STA DCD Timing Violations Check</h1>
                <h2>Overview</h2>
                <p>This checker validates Static Timing Analysis (STA) timing violations...</p>
              </div>
            </div>
            <div className="mt-4">
              <Button variant="secondary" size="sm" className="w-full">
                Download README
              </Button>
            </div>
          </div>
        )}

        {activeTab === 'yaml' && (
          <div>
            <div className="bg-gray-900 rounded-lg p-4 overflow-auto">
              <pre className="text-xs text-gray-100 font-mono whitespace-pre-wrap">
{`item_id: IMP-10-0-0-13
module: 10.0_STA_DCD_CHECK
description: Check for STA timing violations
input_files:
  - timing.rpt
  - sta.log
  - design.sdc`}
              </pre>
            </div>
            <div className="mt-4">
              <Button variant="secondary" size="sm" className="w-full">
                Download YAML
              </Button>
            </div>
          </div>
        )}

        {activeTab === 'tests' && (
          <div className="space-y-4">
            {[
              { name: 'test_parse_setup_violations', status: 'PASSED', duration: '0.23s' },
              { name: 'test_parse_hold_violations', status: 'PASSED', duration: '0.18s' },
              { name: 'test_empty_report', status: 'PASSED', duration: '0.05s' }
            ].map((test, idx) => (
              <div key={idx} className="p-3 border border-gray-200 rounded-lg">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm font-medium text-gray-900">{test.name}</span>
                  <StatusBadge status={test.status} />
                </div>
                <div className="text-xs text-gray-600">Duration: {test.duration}</div>
              </div>
            ))}
            <Button variant="secondary" size="sm" className="w-full">
              Download Test Results
            </Button>
          </div>
        )}
      </div>
    </div>
  )
}
