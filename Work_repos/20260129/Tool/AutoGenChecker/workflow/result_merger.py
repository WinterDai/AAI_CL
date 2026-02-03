"""
Test Result Merger for Comprehensive Testing.

Merges results from multiple test runs:
- Consolidates 6 test types into single report
- Generates summary statistics
- Produces human-readable report
- Exports to multiple formats (JSON, Markdown, HTML)

Storage: Work/test_results/{item_id}/{timestamp}/consolidated_report.*
"""

from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime
import json


class ResultMerger:
    """Merge and analyze test results."""
    
    def __init__(self, results_dir: Path):
        """
        Initialize result merger.
        
        Args:
            results_dir: Directory containing test_results.json
        """
        self.results_dir = results_dir
        
        # Load results
        results_file = results_dir / "test_results.json"
        if not results_file.exists():
            raise FileNotFoundError(f"Results file not found: {results_file}")
        
        with open(results_file, 'r', encoding='utf-8') as f:
            self.results_data = json.load(f)
    
    def generate_consolidated_report(self) -> str:
        """
        Generate comprehensive Markdown report.
        
        Returns:
            Markdown formatted report string
        """
        item_id = self.results_data["item_id"]
        timestamp = self.results_data["timestamp"]
        summary = self.results_data["summary"]
        test_results = self.results_data["test_results"]
        
        report = []
        report.append(f"# Test Report: {item_id}")
        report.append(f"\n**Generated:** {timestamp}")
        report.append(f"**Module:** {self.results_data['module']}")
        report.append(f"**Checker:** `{self.results_data['checker_script']}`")
        
        # Summary section
        report.append("\n---\n")
        report.append("## Summary\n")
        report.append(f"- **Total Tests:** {summary['total_tests']}")
        report.append(f"- **Passed:** {summary['passed']}")
        report.append(f"- **Failed:** {summary['failed']}")
        report.append(f"- **Skipped:** {summary['skipped']}")
        report.append(f"- **Pass Rate:** {summary['pass_rate']}")
        report.append(f"- **Total Time:** {summary['total_execution_time']}")
        
        # Individual test results
        report.append("\n---\n")
        report.append("## Test Results\n")
        
        for test_type, result in test_results.items():
            status = result['status']
            status_icon = self._get_status_icon(status)
            
            report.append(f"\n### {status_icon} {test_type}\n")
            report.append(f"- **Status:** {status}")
            report.append(f"- **Execution Time:** {result['execution_time']:.2f}s")
            report.append(f"- **Timestamp:** {result['timestamp']}")
            
            if result.get('errors'):
                report.append(f"\n**Errors:**")
                report.append(f"```")
                report.append(result['errors'])
                report.append(f"```")
            
            # Link to full output
            output_file = f"{test_type}_output.txt"
            report.append(f"\n📄 [Full Output]({output_file})")
        
        # Pass/Fail analysis
        report.append("\n---\n")
        report.append("## Analysis\n")
        report.append(self._generate_analysis(test_results))
        
        return "\n".join(report)
    
    def _get_status_icon(self, status: str) -> str:
        """Get emoji icon for status."""
        if "PASS" in status.upper():
            return "✅"
        elif "ERROR" in status.upper() or "FAIL" in status.upper():
            return "❌"
        elif "SKIP" in status.upper() or "TIMEOUT" in status.upper():
            return "⚠️"
        else:
            return "❓"
    
    def _generate_analysis(self, test_results: Dict[str, Any]) -> str:
        """Generate analysis of test results."""
        analysis = []
        
        # Count by status
        status_counts = {}
        for result in test_results.values():
            status = result['status']
            status_counts[status] = status_counts.get(status, 0) + 1
        
        analysis.append("### Status Distribution\n")
        for status, count in sorted(status_counts.items()):
            icon = self._get_status_icon(status)
            analysis.append(f"- {icon} {status}: {count}")
        
        # Check for failures
        failed_tests = [
            test_type for test_type, result in test_results.items()
            if "ERROR" in result['status'] or "FAIL" in result['status']
        ]
        
        if failed_tests:
            analysis.append(f"\n### ⚠️ Failed Tests\n")
            for test_type in failed_tests:
                analysis.append(f"- `{test_type}`: {test_results[test_type]['status']}")
                if test_results[test_type].get('errors'):
                    analysis.append(f"  - Error: {test_results[test_type]['errors'][:100]}...")
        else:
            analysis.append(f"\n### ✅ All Tests Passed!\n")
            analysis.append("No failures detected. Checker is working as expected.")
        
        return "\n".join(analysis)
    
    def save_consolidated_report(self) -> Path:
        """
        Save consolidated report to Markdown file.
        
        Returns:
            Path to report file
        """
        report_content = self.generate_consolidated_report()
        
        report_file = self.results_dir / "consolidated_report.md"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report_content)
        
        return report_file
    
    def export_to_html(self) -> Path:
        """
        Export report to HTML format.
        
        Returns:
            Path to HTML file
        """
        md_content = self.generate_consolidated_report()
        
        # Simple Markdown to HTML conversion
        html_content = self._markdown_to_html(md_content)
        
        html_file = self.results_dir / "consolidated_report.html"
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        return html_file
    
    def _markdown_to_html(self, md_content: str) -> str:
        """Simple Markdown to HTML conversion."""
        html = []
        html.append("<!DOCTYPE html>")
        html.append("<html>")
        html.append("<head>")
        html.append("  <meta charset='UTF-8'>")
        html.append("  <title>Test Report</title>")
        html.append("  <style>")
        html.append("    body { font-family: Arial, sans-serif; max-width: 900px; margin: 40px auto; padding: 20px; }")
        html.append("    h1 { color: #2c3e50; border-bottom: 3px solid #3498db; padding-bottom: 10px; }")
        html.append("    h2 { color: #34495e; border-bottom: 2px solid #95a5a6; padding-bottom: 8px; margin-top: 30px; }")
        html.append("    h3 { color: #7f8c8d; margin-top: 20px; }")
        html.append("    code { background-color: #f4f4f4; padding: 2px 6px; border-radius: 3px; }")
        html.append("    pre { background-color: #f9f9f9; padding: 15px; border-radius: 5px; overflow-x: auto; }")
        html.append("    ul { line-height: 1.8; }")
        html.append("    hr { border: none; border-top: 1px solid #ecf0f1; margin: 30px 0; }")
        html.append("  </style>")
        html.append("</head>")
        html.append("<body>")
        
        # Simple conversion (replace with markdown library in production)
        lines = md_content.split('\n')
        in_code_block = False
        
        for line in lines:
            if line.startswith('```'):
                if in_code_block:
                    html.append("</pre>")
                    in_code_block = False
                else:
                    html.append("<pre><code>")
                    in_code_block = True
            elif in_code_block:
                html.append(line)
            elif line.startswith('# '):
                html.append(f"<h1>{line[2:]}</h1>")
            elif line.startswith('## '):
                html.append(f"<h2>{line[3:]}</h2>")
            elif line.startswith('### '):
                html.append(f"<h3>{line[4:]}</h3>")
            elif line.startswith('- '):
                html.append(f"<li>{line[2:]}</li>")
            elif line.startswith('---'):
                html.append("<hr>")
            elif line.startswith('**') and line.endswith('**'):
                html.append(f"<p><strong>{line[2:-2]}</strong></p>")
            elif line.strip():
                html.append(f"<p>{line}</p>")
            else:
                html.append("<br>")
        
        html.append("</body>")
        html.append("</html>")
        
        return "\n".join(html)


def merge_and_report(results_dir: Path) -> Dict[str, Path]:
    """
    Convenience function to merge results and generate reports.
    
    Args:
        results_dir: Directory containing test results
    
    Returns:
        Dict mapping format to file path
    """
    merger = ResultMerger(results_dir)
    
    reports = {}
    reports['markdown'] = merger.save_consolidated_report()
    reports['html'] = merger.export_to_html()
    
    return reports


if __name__ == "__main__":
    # Result merger CLI
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python result_merger.py <results_dir>")
        print("Example: python result_merger.py Work/test_results/IMP-9-0-0-07/20250126_143052")
        sys.exit(1)
    
    results_dir = Path(sys.argv[1])
    
    if not results_dir.exists():
        print(f"❌ Results directory not found: {results_dir}")
        sys.exit(1)
    
    print(f"\nResult Merger")
    print(f"Results Dir: {results_dir}")
    
    try:
        reports = merge_and_report(results_dir)
        
        print(f"\n✅ Generated reports:")
        for format_name, file_path in reports.items():
            print(f"  📄 {format_name}: {file_path.name}")
        
    except Exception as e:
        print(f"\n❌ Failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
