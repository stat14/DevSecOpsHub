"""
Enhanced report generation with advanced templates and analytics
"""
from flask import Blueprint, request, render_template, jsonify, send_file, session
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.graphics.shapes import Drawing
from reportlab.graphics.charts.piecharts import Pie
from reportlab.graphics.charts.linecharts import HorizontalLineChart
from reportlab.graphics.charts.barcharts import VerticalBarChart
from models import User, Project, Finding, Task, db
from auth import require_role
from datetime import datetime, timedelta
import io
import os
import plotly.graph_objs as go
import plotly.io as pio
from PIL import Image as PILImage
import tempfile

enhanced_reports_bp = Blueprint('enhanced_reports', __name__)

class AdvancedReportGenerator:
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self.custom_styles = self._create_custom_styles()
    
    def _create_custom_styles(self):
        """Create custom paragraph styles"""
        styles = {}
        
        # Executive Summary Style
        styles['ExecutiveSummary'] = ParagraphStyle(
            'ExecutiveSummary',
            parent=self.styles['Normal'],
            fontSize=11,
            spaceAfter=12,
            textColor=colors.HexColor('#2c3e50')
        )
        
        # Risk Level Styles
        styles['Critical'] = ParagraphStyle(
            'Critical',
            parent=self.styles['Normal'],
            fontSize=10,
            textColor=colors.HexColor('#e74c3c'),
            fontName='Helvetica-Bold'
        )
        
        styles['High'] = ParagraphStyle(
            'High',
            parent=self.styles['Normal'],
            fontSize=10,
            textColor=colors.HexColor('#f39c12'),
            fontName='Helvetica-Bold'
        )
        
        styles['Medium'] = ParagraphStyle(
            'Medium',
            parent=self.styles['Normal'],
            fontSize=10,
            textColor=colors.HexColor('#f1c40f'),
            fontName='Helvetica-Bold'
        )
        
        styles['Low'] = ParagraphStyle(
            'Low',
            parent=self.styles['Normal'],
            fontSize=10,
            textColor=colors.HexColor('#27ae60'),
            fontName='Helvetica-Bold'
        )
        
        return styles
    
    def generate_comprehensive_security_report(self, project_id, output_path):
        """Generate comprehensive security report with charts and analytics"""
        project = Project.query.get_or_404(project_id)
        findings = Finding.query.filter_by(project_id=project_id).all()
        
        doc = SimpleDocTemplate(output_path, pagesize=A4)
        story = []
        
        # Title Page
        story.extend(self._create_title_page(project))
        story.append(PageBreak())
        
        # Executive Summary
        story.extend(self._create_executive_summary(project, findings))
        story.append(PageBreak())
        
        # Risk Assessment with Charts
        story.extend(self._create_risk_assessment(findings))
        story.append(PageBreak())
        
        # Detailed Findings
        story.extend(self._create_detailed_findings(findings))
        story.append(PageBreak())
        
        # Recommendations
        story.extend(self._create_recommendations(findings))
        story.append(PageBreak())
        
        # Appendices
        story.extend(self._create_appendices(project, findings))
        
        doc.build(story)
        return output_path
    
    def _create_title_page(self, project):
        """Create professional title page"""
        story = []
        
        # Company Logo (if available)
        # story.append(Image('static/images/logo.png', width=2*inch, height=1*inch))
        story.append(Spacer(1, 0.5*inch))
        
        # Title
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=self.styles['Title'],
            fontSize=24,
            textColor=colors.HexColor('#2c3e50'),
            alignment=1  # Center
        )
        story.append(Paragraph("PENETRATION TESTING REPORT", title_style))
        story.append(Spacer(1, 0.5*inch))
        
        # Project Information Table
        project_data = [
            ['Client:', project.client_name or 'N/A'],
            ['Project:', project.name],
            ['Report Date:', datetime.now().strftime('%B %d, %Y')],
            ['Classification:', 'CONFIDENTIAL'],
            ['Version:', '1.0']
        ]
        
        project_table = Table(project_data, colWidths=[2*inch, 4*inch])
        project_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 12),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ]))
        
        story.append(project_table)
        story.append(Spacer(1, 2*inch))
        
        # Disclaimer
        disclaimer_text = """
        <b>CONFIDENTIALITY NOTICE:</b><br/>
        This document contains confidential and proprietary information. 
        Distribution is restricted to authorized personnel only.
        """
        story.append(Paragraph(disclaimer_text, self.styles['Normal']))
        
        return story
    
    def _create_executive_summary(self, project, findings):
        """Create executive summary with key metrics"""
        story = []
        
        story.append(Paragraph("EXECUTIVE SUMMARY", self.styles['Heading1']))
        story.append(Spacer(1, 12))
        
        # Summary text
        summary_text = f"""
        This report presents the findings of a comprehensive penetration test conducted on 
        {project.name} between {project.start_date.strftime('%B %d, %Y') if project.start_date else 'N/A'} 
        and {project.end_date.strftime('%B %d, %Y') if project.end_date else 'Present'}. 
        The assessment identified {len(findings)} security findings requiring attention.
        """
        story.append(Paragraph(summary_text, self.custom_styles['ExecutiveSummary']))
        story.append(Spacer(1, 12))
        
        # Key Findings Summary
        severity_counts = {
            'critical': len([f for f in findings if f.severity == 'critical']),
            'high': len([f for f in findings if f.severity == 'high']),
            'medium': len([f for f in findings if f.severity == 'medium']),
            'low': len([f for f in findings if f.severity == 'low']),
            'informational': len([f for f in findings if f.severity == 'informational'])
        }
        
        findings_data = [
            ['Risk Level', 'Count', 'Percentage'],
            ['Critical', str(severity_counts['critical']), f"{(severity_counts['critical']/len(findings)*100):.1f}%" if findings else "0%"],
            ['High', str(severity_counts['high']), f"{(severity_counts['high']/len(findings)*100):.1f}%" if findings else "0%"],
            ['Medium', str(severity_counts['medium']), f"{(severity_counts['medium']/len(findings)*100):.1f}%" if findings else "0%"],
            ['Low', str(severity_counts['low']), f"{(severity_counts['low']/len(findings)*100):.1f}%" if findings else "0%"],
            ['Informational', str(severity_counts['informational']), f"{(severity_counts['informational']/len(findings)*100):.1f}%" if findings else "0%"]
        ]
        
        findings_table = Table(findings_data, colWidths=[2*inch, 1*inch, 1.5*inch])
        findings_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#34495e')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(findings_table)
        story.append(Spacer(1, 12))
        
        # Risk Assessment Chart
        if findings:
            chart_image = self._create_severity_chart(severity_counts)
            if chart_image:
                story.append(chart_image)
        
        return story
    
    def _create_risk_assessment(self, findings):
        """Create risk assessment section with detailed analysis"""
        story = []
        
        story.append(Paragraph("RISK ASSESSMENT", self.styles['Heading1']))
        story.append(Spacer(1, 12))
        
        # Risk Methodology
        methodology_text = """
        <b>Risk Rating Methodology:</b><br/>
        Vulnerabilities are rated using a combination of CVSS v3.1 scoring and business impact assessment.
        The following criteria are used to determine risk levels:
        """
        story.append(Paragraph(methodology_text, self.styles['Normal']))
        story.append(Spacer(1, 12))
        
        # Risk Levels Table
        risk_data = [
            ['Risk Level', 'CVSS Score', 'Description'],
            ['Critical', '9.0 - 10.0', 'Immediate threat requiring urgent remediation'],
            ['High', '7.0 - 8.9', 'Significant risk requiring prompt attention'],
            ['Medium', '4.0 - 6.9', 'Moderate risk requiring planned remediation'],
            ['Low', '0.1 - 3.9', 'Minimal risk requiring monitoring'],
            ['Info', '0.0', 'Informational findings for awareness']
        ]
        
        risk_table = Table(risk_data, colWidths=[1.5*inch, 1.5*inch, 3*inch])
        risk_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#34495e')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(risk_table)
        story.append(Spacer(1, 12))
        
        # Business Impact Assessment
        if findings:
            critical_high_findings = [f for f in findings if f.severity in ['critical', 'high']]
            if critical_high_findings:
                impact_text = f"""
                <b>Business Impact:</b><br/>
                The {len(critical_high_findings)} critical and high-risk vulnerabilities identified pose 
                significant threats to the organization's security posture. Immediate remediation is 
                recommended to prevent potential security incidents.
                """
                story.append(Paragraph(impact_text, self.styles['Normal']))
        
        return story
    
    def _create_detailed_findings(self, findings):
        """Create detailed findings section"""
        story = []
        
        story.append(Paragraph("DETAILED FINDINGS", self.styles['Heading1']))
        story.append(Spacer(1, 12))
        
        # Sort findings by severity
        severity_order = {'critical': 0, 'high': 1, 'medium': 2, 'low': 3, 'informational': 4}
        sorted_findings = sorted(findings, key=lambda f: severity_order.get(f.severity, 5))
        
        for i, finding in enumerate(sorted_findings, 1):
            # Finding Header
            finding_title = f"{i}. {finding.title}"
            story.append(Paragraph(finding_title, self.styles['Heading2']))
            story.append(Spacer(1, 6))
            
            # Finding Details Table
            finding_data = [
                ['Risk Level:', finding.severity.title()],
                ['CVSS Score:', finding.cvss_score or 'N/A'],
                ['Status:', finding.status.title()],
                ['Affected Component:', finding.affected_component or 'N/A']
            ]
            
            finding_table = Table(finding_data, colWidths=[2*inch, 4*inch])
            finding_table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ]))
            
            story.append(finding_table)
            story.append(Spacer(1, 12))
            
            # Description
            if finding.description:
                story.append(Paragraph("<b>Description:</b>", self.styles['Normal']))
                story.append(Paragraph(finding.description, self.styles['Normal']))
                story.append(Spacer(1, 12))
            
            # Impact
            if finding.impact:
                story.append(Paragraph("<b>Impact:</b>", self.styles['Normal']))
                story.append(Paragraph(finding.impact, self.styles['Normal']))
                story.append(Spacer(1, 12))
            
            # Remediation
            if finding.remediation:
                story.append(Paragraph("<b>Remediation:</b>", self.styles['Normal']))
                story.append(Paragraph(finding.remediation, self.styles['Normal']))
                story.append(Spacer(1, 12))
            
            # References
            if finding.references:
                story.append(Paragraph("<b>References:</b>", self.styles['Normal']))
                story.append(Paragraph(finding.references, self.styles['Normal']))
                story.append(Spacer(1, 12))
            
            if i < len(sorted_findings):
                story.append(Spacer(1, 12))
        
        return story
    
    def _create_recommendations(self, findings):
        """Create recommendations section"""
        story = []
        
        story.append(Paragraph("RECOMMENDATIONS", self.styles['Heading1']))
        story.append(Spacer(1, 12))
        
        # Priority Recommendations
        critical_findings = [f for f in findings if f.severity == 'critical']
        high_findings = [f for f in findings if f.severity == 'high']
        
        if critical_findings:
            story.append(Paragraph("Critical Priority Actions:", self.styles['Heading2']))
            for finding in critical_findings:
                story.append(Paragraph(f"• {finding.title}: {finding.remediation or 'Immediate remediation required'}", self.styles['Normal']))
            story.append(Spacer(1, 12))
        
        if high_findings:
            story.append(Paragraph("High Priority Actions:", self.styles['Heading2']))
            for finding in high_findings:
                story.append(Paragraph(f"• {finding.title}: {finding.remediation or 'Prompt remediation required'}", self.styles['Normal']))
            story.append(Spacer(1, 12))
        
        # Strategic Recommendations
        strategic_text = """
        <b>Strategic Security Recommendations:</b><br/>
        1. Implement a comprehensive security awareness training program<br/>
        2. Establish regular security assessments and penetration testing<br/>
        3. Deploy advanced threat detection and monitoring solutions<br/>
        4. Develop and maintain an incident response plan<br/>
        5. Conduct regular security architecture reviews
        """
        story.append(Paragraph(strategic_text, self.styles['Normal']))
        
        return story
    
    def _create_appendices(self, project, findings):
        """Create appendices section"""
        story = []
        
        story.append(Paragraph("APPENDICES", self.styles['Heading1']))
        story.append(Spacer(1, 12))
        
        # Tools Used
        story.append(Paragraph("A. Tools and Methodologies Used", self.styles['Heading2']))
        tools_text = """
        The following tools and methodologies were used during the assessment:
        • Nmap - Network discovery and port scanning
        • Burp Suite Professional - Web application security testing
        • OWASP ZAP - Automated vulnerability scanning
        • Metasploit Framework - Exploitation and post-exploitation
        • Custom scripts and manual testing techniques
        """
        story.append(Paragraph(tools_text, self.styles['Normal']))
        story.append(Spacer(1, 12))
        
        # Glossary
        story.append(Paragraph("B. Glossary", self.styles['Heading2']))
        glossary_text = """
        <b>CVSS:</b> Common Vulnerability Scoring System - A standardized method for rating vulnerabilities<br/>
        <b>CWE:</b> Common Weakness Enumeration - A community-developed dictionary of software weaknesses<br/>
        <b>POC:</b> Proof of Concept - Demonstration that a vulnerability can be exploited<br/>
        <b>OWASP:</b> Open Web Application Security Project - A nonprofit foundation focused on improving software security
        """
        story.append(Paragraph(glossary_text, self.styles['Normal']))
        
        return story
    
    def _create_severity_chart(self, severity_counts):
        """Create severity distribution pie chart"""
        try:
            # Create Plotly pie chart
            labels = []
            values = []
            colors_list = []
            
            color_map = {
                'critical': '#e74c3c',
                'high': '#f39c12', 
                'medium': '#f1c40f',
                'low': '#27ae60',
                'informational': '#3498db'
            }
            
            for severity, count in severity_counts.items():
                if count > 0:
                    labels.append(severity.title())
                    values.append(count)
                    colors_list.append(color_map[severity])
            
            if not values:
                return None
            
            fig = go.Figure(data=[go.Pie(
                labels=labels,
                values=values,
                marker_colors=colors_list,
                textinfo='label+percent',
                hole=0.3
            )])
            
            fig.update_layout(
                title="Finding Distribution by Severity",
                font=dict(size=14),
                width=400,
                height=300
            )
            
            # Save as image
            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
                pio.write_image(fig, tmp.name, width=400, height=300)
                return Image(tmp.name, width=4*inch, height=3*inch)
                
        except Exception as e:
            print(f"Error creating chart: {e}")
            return None

# API Routes
@enhanced_reports_bp.route('/generate/<int:project_id>')
@require_role(['admin', 'super_admin', 'pentester'])
def generate_enhanced_report(project_id):
    """Generate enhanced security report"""
    try:
        generator = AdvancedReportGenerator()
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
            output_path = tmp.name
        
        # Generate report
        generator.generate_comprehensive_security_report(project_id, output_path)
        
        return send_file(
            output_path,
            as_attachment=True,
            download_name=f"security_report_{project_id}_{datetime.now().strftime('%Y%m%d')}.pdf",
            mimetype='application/pdf'
        )
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@enhanced_reports_bp.route('/template/<template_type>')
@require_role(['admin', 'super_admin'])
def get_report_template(template_type):
    """Get report template for customization"""
    templates = {
        'security': {
            'name': 'Security Assessment Report',
            'sections': [
                'Executive Summary',
                'Scope and Methodology', 
                'Risk Assessment',
                'Detailed Findings',
                'Recommendations',
                'Appendices'
            ],
            'required_fields': ['client_name', 'project_name', 'assessment_dates']
        },
        'compliance': {
            'name': 'Compliance Assessment Report',
            'sections': [
                'Executive Summary',
                'Compliance Framework',
                'Assessment Results',
                'Gap Analysis',
                'Remediation Plan'
            ],
            'required_fields': ['framework', 'scope', 'assessment_period']
        }
    }
    
    return jsonify(templates.get(template_type, {}))