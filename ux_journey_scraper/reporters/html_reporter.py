"""
HTML reporter for interactive journey analysis reports.
"""
import base64
from pathlib import Path
from datetime import datetime


class HTMLReporter:
    """Generate interactive HTML reports from journey analysis."""

    def generate_report(self, analysis, journey, output_path, include_screenshots=True):
        """
        Generate interactive HTML report.

        Args:
            analysis: JourneyAnalysis object
            journey: Journey object
            output_path: Path to save HTML file
            include_screenshots: Whether to embed screenshots

        Returns:
            str: Path to generated report
        """
        html = self._build_html(analysis, journey, include_screenshots)

        # Save to file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html)

        print(f"✓ HTML report saved: {output_path}")
        return str(output_path)

    def _build_html(self, analysis, journey, include_screenshots):
        """Build the complete HTML report."""
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Journey Analysis Report - {journey.start_url}</title>
    <style>
        {self._get_css()}
    </style>
</head>
<body>
    <div class="container">
        {self._build_header(analysis, journey)}
        {self._build_summary(analysis)}
        {self._build_steps_section(analysis, journey, include_screenshots)}
        {self._build_footer()}
    </div>
</body>
</html>"""
        return html

    def _get_css(self):
        """Get CSS styles for the report."""
        return """
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            background: #f5f5f5;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }
        
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px;
            border-radius: 10px;
            margin-bottom: 30px;
        }
        
        .header h1 {
            font-size: 32px;
            margin-bottom: 10px;
        }
        
        .header .url {
            font-size: 14px;
            opacity: 0.9;
        }
        
        .summary {
            background: white;
            padding: 30px;
            border-radius: 10px;
            margin-bottom: 30px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        
        .summary h2 {
            margin-bottom: 20px;
            color: #667eea;
        }
        
        .stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
        }
        
        .stat {
            text-align: center;
            padding: 20px;
            background: #f8f9fa;
            border-radius: 8px;
        }
        
        .stat-value {
            font-size: 36px;
            font-weight: bold;
            color: #667eea;
        }
        
        .stat-label {
            font-size: 14px;
            color: #666;
            margin-top: 5px;
        }
        
        .score-excellent {
            color: #28a745 !important;
        }
        
        .score-good {
            color: #ffc107 !important;
        }
        
        .score-poor {
            color: #dc3545 !important;
        }
        
        .step {
            background: white;
            padding: 30px;
            border-radius: 10px;
            margin-bottom: 20px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        
        .step-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
            padding-bottom: 15px;
            border-bottom: 2px solid #f0f0f0;
        }
        
        .step-number {
            background: #667eea;
            color: white;
            width: 40px;
            height: 40px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: bold;
        }
        
        .step-title {
            flex: 1;
            margin-left: 20px;
        }
        
        .step-title h3 {
            font-size: 20px;
            margin-bottom: 5px;
        }
        
        .step-title .url {
            font-size: 13px;
            color: #666;
        }
        
        .step-score {
            font-size: 28px;
            font-weight: bold;
        }
        
        .screenshot {
            width: 100%;
            border-radius: 8px;
            margin: 20px 0;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        
        .issues {
            margin-top: 20px;
        }
        
        .issue {
            padding: 15px;
            margin-bottom: 10px;
            border-left: 4px solid;
            background: #f8f9fa;
            border-radius: 4px;
        }
        
        .issue-critical {
            border-color: #dc3545;
            background: #f8d7da;
        }
        
        .issue-major {
            border-color: #ffc107;
            background: #fff3cd;
        }
        
        .issue-minor {
            border-color: #17a2b8;
            background: #d1ecf1;
        }
        
        .issue-title {
            font-weight: bold;
            margin-bottom: 5px;
        }
        
        .issue-fix {
            font-size: 14px;
            color: #666;
            margin-top: 5px;
        }
        
        .badge {
            display: inline-block;
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 12px;
            font-weight: bold;
            margin-right: 5px;
        }
        
        .badge-critical {
            background: #dc3545;
            color: white;
        }
        
        .badge-major {
            background: #ffc107;
            color: #333;
        }
        
        .badge-minor {
            background: #17a2b8;
            color: white;
        }
        
        .footer {
            text-align: center;
            padding: 20px;
            color: #666;
            font-size: 14px;
        }
        
        .no-issues {
            padding: 20px;
            background: #d4edda;
            border-left: 4px solid #28a745;
            border-radius: 4px;
            color: #155724;
        }
        """

    def _build_header(self, analysis, journey):
        """Build report header."""
        return f"""
        <div class="header">
            <h1>🎯 Journey Analysis Report</h1>
            <div class="url">Start URL: {journey.start_url}</div>
            <div class="url">Analyzed: {datetime.fromisoformat(analysis.analysis_timestamp).strftime('%B %d, %Y at %I:%M %p')}</div>
        </div>
        """

    def _build_summary(self, analysis):
        """Build summary section."""
        score_class = self._get_score_class(analysis.overall_score)
        
        return f"""
        <div class="summary">
            <h2>📊 Journey Summary</h2>
            <div class="stats">
                <div class="stat">
                    <div class="stat-value {score_class}">{analysis.overall_score}</div>
                    <div class="stat-label">Overall Score</div>
                </div>
                <div class="stat">
                    <div class="stat-value">{len(analysis.step_analyses)}</div>
                    <div class="stat-label">Total Steps</div>
                </div>
                <div class="stat">
                    <div class="stat-value">{analysis.total_violations}</div>
                    <div class="stat-label">UX Violations</div>
                </div>
                <div class="stat">
                    <div class="stat-value">{analysis.total_accessibility_issues}</div>
                    <div class="stat-label">A11y Issues</div>
                </div>
            </div>
        </div>
        """

    def _build_steps_section(self, analysis, journey, include_screenshots):
        """Build steps section."""
        steps_html = ""
        
        for step_analysis in analysis.step_analyses:
            # Find corresponding journey step for screenshot
            journey_step = next((s for s in journey.steps if s.step_number == step_analysis.step_number), None)
            
            steps_html += self._build_step(step_analysis, journey_step, include_screenshots)
        
        return steps_html

    def _build_step(self, step_analysis, journey_step, include_screenshot):
        """Build individual step section."""
        score_class = self._get_score_class(step_analysis.overall_score)
        
        # Build screenshot HTML
        screenshot_html = ""
        if include_screenshot and journey_step and journey_step.screenshot_path:
            try:
                screenshot_path = Path(journey_step.screenshot_path)
                if screenshot_path.exists():
                    with open(screenshot_path, 'rb') as f:
                        img_data = base64.b64encode(f.read()).decode('utf-8')
                    screenshot_html = f'<img src="data:image/png;base64,{img_data}" class="screenshot" alt="Step {step_analysis.step_number} screenshot">'
            except Exception as e:
                screenshot_html = f'<p style="color: #666;">Screenshot unavailable: {e}</p>'
        
        # Build issues HTML
        issues_html = self._build_issues_html(step_analysis)
        
        return f"""
        <div class="step">
            <div class="step-header">
                <div class="step-number">{step_analysis.step_number}</div>
                <div class="step-title">
                    <h3>{step_analysis.title}</h3>
                    <div class="url">{step_analysis.url}</div>
                    <div style="margin-top: 5px;">
                        <span class="badge" style="background: #6c757d; color: white;">{step_analysis.page_type}</span>
                    </div>
                </div>
                <div class="step-score {score_class}">{step_analysis.overall_score}</div>
            </div>
            
            {screenshot_html}
            
            {issues_html}
        </div>
        """

    def _build_issues_html(self, step_analysis):
        """Build issues HTML for a step."""
        total_issues = len(step_analysis.ux_violations) + len(step_analysis.accessibility_issues)
        
        if total_issues == 0:
            return '<div class="no-issues">✅ No issues found on this page!</div>'
        
        html = '<div class="issues">'
        
        # UX Violations
        if step_analysis.ux_violations:
            html += '<h4 style="margin-bottom: 10px;">UX Violations</h4>'
            for violation in step_analysis.ux_violations:
                severity = violation.get('severity', 'minor')
                guideline_id = violation.get('guideline_id', '')
                issue = violation.get('issue', '')
                fix = violation.get('fix', '')
                
                html += f"""
                <div class="issue issue-{severity}">
                    <div class="issue-title">
                        <span class="badge badge-{severity}">{severity.upper()}</span>
                        {f'Guideline #{guideline_id}: ' if guideline_id else ''}{issue}
                    </div>
                    <div class="issue-fix">💡 Fix: {fix}</div>
                </div>
                """
        
        # Accessibility Issues
        if step_analysis.accessibility_issues:
            html += '<h4 style="margin: 20px 0 10px 0;">Accessibility Issues</h4>'
            for issue in step_analysis.accessibility_issues:
                severity = issue.get('severity', 'minor')
                wcag = issue.get('wcag_criterion', '')
                issue_text = issue.get('issue', '')
                fix = issue.get('fix', '')
                
                html += f"""
                <div class="issue issue-{severity}">
                    <div class="issue-title">
                        <span class="badge badge-{severity}">{severity.upper()}</span>
                        {f'WCAG {wcag}: ' if wcag else ''}{issue_text}
                    </div>
                    <div class="issue-fix">💡 Fix: {fix}</div>
                </div>
                """
        
        html += '</div>'
        return html

    def _build_footer(self):
        """Build report footer."""
        return f"""
        <div class="footer">
            Generated by <strong>UX Journey Scraper</strong> • {datetime.now().strftime('%Y')}
        </div>
        """

    def _get_score_class(self, score):
        """Get CSS class based on score."""
        if score >= 90:
            return 'score-excellent'
        elif score >= 75:
            return 'score-good'
        else:
            return 'score-poor'
