"""
Regression Reporter for Test Results.

Generates comprehensive regression reports:
- Executive summary (PASS/FAIL, regression count)
- Detailed regression list with severity
- Improvement highlights
- Output diff visualization
- Exports to Markdown and HTML

Output: regression_report.md/html in test results directory
"""

from pathlib import Path
from typing import Dict, Any
from datetime import datetime


class RegressionReporter:
    """Generate regression test reports."""
    
    def __init__(self, item_id: str, diff_data: Dict[str, Any]):
        """
        Initialize regression reporter.
        
        Args:
            item_id: Checker ID
            diff_data: Diff data from regression_diff.py
        """
        self.item_id = item_id
        self.diff_data = diff_data
    
    def generate_markdown_report(self) -> str:
        """
        Generate comprehensive Markdown report.
        
        Returns:
            Markdown formatted report string
        """
        report = []
        
        # Header
        report.append(f"# Regression Test Report: {self.item_id}")
        report.append(f"\n**Generated:** {self.diff_data['comparison_time']}")
        report.append(f"**Overall Status:** {self._format_overall_status()}")
        
        # Executive Summary
        report.append("\n---\n")
        report.append("## Executive Summary\n")
        
        baseline_info = self.diff_data['baseline_info']
        current_info = self.diff_data['current_info']
        
        report.append("### Baseline")
        report.append(f"- **Created:** {baseline_info['created']}")
        report.append(f"- **Description:** {baseline_info['description']}")
        report.append(f"- **Pass Rate:** {baseline_info['pass_rate']}")
        
        report.append("\n### Current Run")
        report.append(f"- **Total Tests:** {current_info['total_tests']}")
        report.append(f"- **Pass Rate:** {current_info['pass_rate']}")
        
        # Pass rate comparison
        baseline_rate = float(baseline_info['pass_rate'].rstrip('%'))
        current_rate = float(current_info['pass_rate'].rstrip('%'))
        rate_diff = current_rate - baseline_rate
        
        if rate_diff > 0:
            report.append(f"- **Pass Rate Change:** +{rate_diff:.1f}% 📈 (Improvement)")
        elif rate_diff < 0:
            report.append(f"- **Pass Rate Change:** {rate_diff:.1f}% 📉 (Regression)")
        else:
            report.append(f"- **Pass Rate Change:** 0% (Unchanged)")
        
        # Regression Section
        if self.diff_data['regressions']:
            report.append("\n---\n")
            report.append("## ❌ Regressions Detected\n")
            report.append(f"**Count:** {len(self.diff_data['regressions'])}\n")
            
            # Group by severity
            critical = [r for r in self.diff_data['regressions'] if r['severity'] == 'CRITICAL']
            high = [r for r in self.diff_data['regressions'] if r['severity'] == 'HIGH']
            medium = [r for r in self.diff_data['regressions'] if r['severity'] == 'MEDIUM']
            low = [r for r in self.diff_data['regressions'] if r['severity'] == 'LOW']
            
            if critical:
                report.append("### 🔴 Critical Regressions\n")
                for reg in critical:
                    report.append(self._format_regression(reg))
            
            if high:
                report.append("### 🟠 High Priority Regressions\n")
                for reg in high:
                    report.append(self._format_regression(reg))
            
            if medium:
                report.append("### 🟡 Medium Priority Regressions\n")
                for reg in medium:
                    report.append(self._format_regression(reg))
            
            if low:
                report.append("### 🔵 Low Priority Regressions\n")
                for reg in low:
                    report.append(self._format_regression(reg))
        
        # Improvement Section
        if self.diff_data['improvements']:
            report.append("\n---\n")
            report.append("## ✅ Improvements\n")
            report.append(f"**Count:** {len(self.diff_data['improvements'])}\n")
            
            for imp in self.diff_data['improvements']:
                report.append(f"- **{imp['test_type']}**: {imp['old_status']} → {imp['new_status']}")
        
        # Unchanged Section
        if self.diff_data['unchanged']:
            report.append("\n---\n")
            report.append("## ➡️ Unchanged Tests\n")
            report.append(f"**Count:** {len(self.diff_data['unchanged'])}\n")
            report.append(f"Tests: {', '.join(self.diff_data['unchanged'])}")
        
        # Output Diff Section
        if self.diff_data['output_diffs']:
            report.append("\n---\n")
            report.append("## 📝 Output Differences\n")
            
            for test_type, diff in self.diff_data['output_diffs'].items():
                report.append(f"\n### {test_type}\n")
                
                if diff.get('count_changed'):
                    report.append("**Item Count Changes:**")
                    baseline_counts = diff['baseline_counts']
                    current_counts = diff['current_counts']
                    
                    all_keys = set(baseline_counts.keys()) | set(current_counts.keys())
                    for key in sorted(all_keys):
                        old = baseline_counts.get(key, 0)
                        new = current_counts.get(key, 0)
                        if old != new:
                            change_icon = "📈" if new > old else "📉"
                            report.append(f"- {key}: {old} → {new} {change_icon}")
                
                report.append(f"\n**Baseline Output Preview:**")
                report.append(f"```")
                report.append(diff['baseline_preview'])
                report.append(f"```")
                
                report.append(f"\n**Current Output Preview:**")
                report.append(f"```")
                report.append(diff['current_preview'])
                report.append(f"```")
        
        # Conclusion
        report.append("\n---\n")
        report.append("## Conclusion\n")
        report.append(self._generate_conclusion())
        
        return "\n".join(report)
    
    def _format_overall_status(self) -> str:
        """Format overall status with emoji."""
        status = self.diff_data['overall_status']
        if status == "REGRESSION":
            return "❌ **REGRESSION** (New failures detected)"
        elif status == "IMPROVEMENT":
            return "✅ **IMPROVEMENT** (Tests now passing)"
        else:
            return "➡️ **UNCHANGED** (No status changes)"
    
    def _format_regression(self, reg: Dict[str, Any]) -> str:
        """Format a single regression entry."""
        test_type = reg['test_type']
        old_status = reg['old_status']
        new_status = reg['new_status']
        severity = reg['severity']
        
        return f"- **{test_type}**: {old_status} → {new_status} (Severity: {severity})\n"
    
    def _generate_conclusion(self) -> str:
        """Generate conclusion based on diff data."""
        overall_status = self.diff_data['overall_status']
        
        if overall_status == "REGRESSION":
            conclusion = [
                "⚠️ **Action Required:** Regressions detected in this test run.",
                "",
                "**Recommended Actions:**",
                "1. Review regression details above",
                "2. Investigate root cause of status changes",
                "3. Fix critical and high priority regressions first",
                "4. Re-run tests after fixes",
                "5. Update baseline once all regressions resolved",
            ]
        elif overall_status == "IMPROVEMENT":
            conclusion = [
                "✅ **Positive Results:** Tests show improvement over baseline.",
                "",
                "**Recommended Actions:**",
                "1. Verify improvements are intentional",
                "2. Review test changes if unexpected",
                "3. Consider updating baseline to capture improvements",
            ]
        else:
            conclusion = [
                "✅ **Stable:** Test results match baseline. No regressions detected.",
                "",
                "All tests behaving consistently with previous run.",
            ]
        
        return "\n".join(conclusion)
    
    def save_report(self, output_dir: Path) -> Path:
        """
        Save regression report to Markdown file.
        
        Args:
            output_dir: Directory to save report
        
        Returns:
            Path to report file
        """
        report_content = self.generate_markdown_report()
        
        report_file = output_dir / "regression_report.md"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report_content)
        
        return report_file
    
    def export_to_html(self, output_dir: Path) -> Path:
        """
        Export report to HTML format.
        
        Args:
            output_dir: Directory to save HTML
        
        Returns:
            Path to HTML file
        """
        md_content = self.generate_markdown_report()
        
        # Simple Markdown to HTML
        html = []
        html.append("<!DOCTYPE html>")
        html.append("<html>")
        html.append("<head>")
        html.append("  <meta charset='UTF-8'>")
        html.append("  <title>Regression Test Report</title>")
        html.append("  <style>")
        html.append("    body { font-family: 'Segoe UI', Arial, sans-serif; max-width: 1000px; margin: 40px auto; padding: 20px; background: #f5f5f5; }")
        html.append("    .container { background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }")
        html.append("    h1 { color: #2c3e50; border-bottom: 3px solid #3498db; padding-bottom: 15px; }")
        html.append("    h2 { color: #34495e; border-bottom: 2px solid #95a5a6; padding-bottom: 10px; margin-top: 30px; }")
        html.append("    h3 { color: #7f8c8d; margin-top: 20px; }")
        html.append("    .status-badge { display: inline-block; padding: 5px 12px; border-radius: 4px; font-weight: bold; }")
        html.append("    .status-regression { background: #e74c3c; color: white; }")
        html.append("    .status-improvement { background: #27ae60; color: white; }")
        html.append("    .status-unchanged { background: #95a5a6; color: white; }")
        html.append("    code { background-color: #f4f4f4; padding: 2px 6px; border-radius: 3px; font-family: 'Courier New', monospace; }")
        html.append("    pre { background-color: #f9f9f9; padding: 15px; border-radius: 5px; overflow-x: auto; border: 1px solid #ddd; }")
        html.append("    ul { line-height: 1.8; }")
        html.append("    hr { border: none; border-top: 1px solid #ecf0f1; margin: 30px 0; }")
        html.append("    .regression-item { background: #fff5f5; padding: 10px; margin: 8px 0; border-left: 4px solid #e74c3c; border-radius: 4px; }")
        html.append("    .improvement-item { background: #f0fff4; padding: 10px; margin: 8px 0; border-left: 4px solid #27ae60; border-radius: 4px; }")
        html.append("  </style>")
        html.append("</head>")
        html.append("<body>")
        html.append("<div class='container'>")
        
        # Convert markdown to HTML (simple version)
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
            elif line.strip():
                html.append(f"<p>{line}</p>")
        
        html.append("</div>")
        html.append("</body>")
        html.append("</html>")
        
        html_file = output_dir / "regression_report.html"
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write("\n".join(html))
        
        return html_file


def generate_regression_report(
    item_id: str,
    diff_data: Dict[str, Any],
    output_dir: Optional[Path] = None,
) -> Path:
    """
    Convenience function to generate regression report.
    
    Args:
        item_id: Checker ID
        diff_data: Diff data from regression_diff.py
        output_dir: Optional output directory (default: current results dir)
    
    Returns:
        Path to Markdown report
    """
    reporter = RegressionReporter(item_id, diff_data)
    
    if output_dir is None:
        # Use current results directory
        try:
            from utils.paths import discover_project_paths
        except ImportError:
            from AutoGenChecker.utils.paths import discover_project_paths
        
        paths = discover_project_paths()
        test_results_base = paths.workspace_root / "Work" / "test_results" / item_id
        output_dir = sorted(test_results_base.glob("*"))[-1]
    
    report_file = reporter.save_report(output_dir)
    html_file = reporter.export_to_html(output_dir)
    
    print(f"✅ Regression reports generated:")
    print(f"   📄 Markdown: {report_file.name}")
    print(f"   🌐 HTML: {html_file.name}")
    
    return report_file


if __name__ == "__main__":
    # Regression reporter CLI
    import sys
    import json
    
    if len(sys.argv) < 2:
        print("Usage: python regression_reporter.py <diff_data_json_file>")
        print("Example: python regression_reporter.py Work/test_results/IMP-9-0-0-07/20250126_143052/regression_diff.json")
        sys.exit(1)
    
    diff_file = Path(sys.argv[1])
    
    if not diff_file.exists():
        print(f"❌ Diff data file not found: {diff_file}")
        sys.exit(1)
    
    with open(diff_file, 'r', encoding='utf-8') as f:
        diff_data = json.load(f)
    
    item_id = diff_data['item_id']
    output_dir = diff_file.parent
    
    print(f"\nRegression Reporter")
    print(f"Item: {item_id}")
    print(f"Output Dir: {output_dir}")
    
    try:
        report_file = generate_regression_report(item_id, diff_data, output_dir)
        print(f"\n✅ Report generated successfully")
    except Exception as e:
        print(f"\n❌ Failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
