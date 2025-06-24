from flask import Blueprint, send_file, flash, redirect, url_for, session
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.colors import black, white, red, orange, yellow, green, blue
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from models import User, Project, Finding, UserProject
from app import db
from auth import require_auth, require_role
from datetime import datetime
import io
import os

reports_bp = Blueprint('reports', __name__)

@reports_bp.route('/pentest/<int:project_id>/pdf')
@require_auth
@require_role(['admin', 'super_admin', 'pentester', 'client'])
def generate_pentest_report(project_id):
    project = Project.query.get_or_404(project_id)
    user = User.query.get(session['user_id'])
    
    # Check access
    if user.role == 'client':
        if not UserProject.query.filter_by(user_id=user.id, project_id=project_id).first():
            flash('Access denied to this project', 'danger')
            return redirect(url_for('client.dashboard'))
    elif user.role in ['pentester']:
        if not UserProject.query.filter_by(user_id=user.id, project_id=project_id).first():
            flash('Access denied to this project', 'danger')
            return redirect(url_for('secure.dashboard'))
    
    # Get findings
    findings = Finding.query.filter_by(project_id=project_id).all()
    
    # Create PDF
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=72, leftMargin=72,
                          topMargin=72, bottomMargin=18)
    
    # Get styles
    styles = getSampleStyleSheet()
    story = []
    
    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        spaceAfter=30,
        alignment=TA_CENTER,
        textColor=black
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=16,
        spaceAfter=12,
        spaceBefore=12,
        textColor=black
    )
    
    # Cover Page
    story.append(Paragraph("Penetration Testing Report", title_style))
    story.append(Spacer(1, 0.5*inch))
    
    # Document control table
    doc_data = [
        ['Document Information', ''],
        ['Document Title', 'Penetration Testing Report'],
        ['Client', project.client_name or 'N/A'],
        ['Project Name', project.name],
        ['Document Version', '1.0'],
        ['Date', datetime.now().strftime('%B %d, %Y')],
        ['Classification', 'Confidential']
    ]
    
    doc_table = Table(doc_data, colWidths=[2*inch, 3*inch])
    doc_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, 0), orange),
        ('TEXTCOLOR', (0, 0), (0, 0), white),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ('BACKGROUND', (0, 1), (-1, -1), white),
        ('GRID', (0, 0), (-1, -1), 1, black)
    ]))
    
    story.append(doc_table)
    story.append(PageBreak())
    
    # Executive Summary
    story.append(Paragraph("1. Executive Summary", heading_style))
    
    # Calculate statistics
    total_findings = len(findings)
    critical_count = len([f for f in findings if f.severity == 'critical'])
    high_count = len([f for f in findings if f.severity == 'high'])
    medium_count = len([f for f in findings if f.severity == 'medium'])
    low_count = len([f for f in findings if f.severity == 'low'])
    info_count = len([f for f in findings if f.severity == 'informational'])
    
    summary_text = f"""
    This report presents the findings of a penetration test conducted on {project.client_name}'s {project.name} 
    system. The assessment was performed to identify security vulnerabilities that could potentially be exploited 
    by malicious actors.
    
    <b>Key Findings</b><br/>
    • A total of {total_findings} vulnerabilities were identified<br/>
    • {critical_count} Critical vulnerabilities<br/>
    • {high_count} High-risk vulnerabilities<br/>
    • {medium_count} Medium-risk vulnerabilities<br/>
    • {low_count} Low-risk vulnerabilities<br/>
    • {info_count} Informational findings
    """
    
    story.append(Paragraph(summary_text, styles['Normal']))
    story.append(Spacer(1, 0.3*inch))
    
    # Critical and High-Risk Issues
    critical_high_findings = [f for f in findings if f.severity in ['critical', 'high']]
    if critical_high_findings:
        story.append(Paragraph("Critical and High-Risk Issues", styles['Heading3']))
        story.append(Paragraph("The most significant security issues identified during the assessment include:", styles['Normal']))
        
        for i, finding in enumerate(critical_high_findings[:5], 1):  # Show top 5
            story.append(Paragraph(f"{i}. <b>{finding.title}</b>: {finding.description[:200]}{'...' if len(finding.description) > 200 else ''}", styles['Normal']))
        
        story.append(Spacer(1, 0.3*inch))
    
    # Risk Distribution Table
    story.append(Paragraph("2. Findings Summary", heading_style))
    
    risk_data = [
        ['Risk Level', 'Count', 'Percentage'],
        ['Critical', str(critical_count), f"{(critical_count/total_findings*100):.1f}%" if total_findings > 0 else "0%"],
        ['High', str(high_count), f"{(high_count/total_findings*100):.1f}%" if total_findings > 0 else "0%"],
        ['Medium', str(medium_count), f"{(medium_count/total_findings*100):.1f}%" if total_findings > 0 else "0%"],
        ['Low', str(low_count), f"{(low_count/total_findings*100):.1f}%" if total_findings > 0 else "0%"],
        ['Informational', str(info_count), f"{(info_count/total_findings*100):.1f}%" if total_findings > 0 else "0%"]
    ]
    
    risk_table = Table(risk_data, colWidths=[2*inch, 1*inch, 1.5*inch])
    risk_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), orange),
        ('TEXTCOLOR', (0, 0), (-1, 0), white),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ('BACKGROUND', (0, 1), (-1, -1), white),
        ('GRID', (0, 0), (-1, -1), 1, black)
    ]))
    
    story.append(risk_table)
    story.append(PageBreak())
    
    # Detailed Findings
    story.append(Paragraph("3. Detailed Findings", heading_style))
    
    severity_colors = {
        'critical': red,
        'high': orange,
        'medium': yellow,
        'low': green,
        'informational': blue
    }
    
    for i, finding in enumerate(findings, 1):
        story.append(Paragraph(f"3.{i} {finding.title}", styles['Heading3']))
        
        # Finding details table
        finding_data = [
            ['Risk Level', finding.severity.title()],
            ['Status', finding.status.title()],
            ['CVSS Score', str(finding.cvss_score) if finding.cvss_score else 'N/A'],
            ['CWE', finding.cwe_id if finding.cwe_id else 'N/A'],
            ['Affected URL', finding.affected_url if finding.affected_url else 'N/A']
        ]
        
        finding_table = Table(finding_data, colWidths=[1.5*inch, 3*inch])
        finding_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), severity_colors.get(finding.severity, black)),
            ('TEXTCOLOR', (0, 0), (0, -1), white),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('BACKGROUND', (1, 0), (1, -1), white),
            ('GRID', (0, 0), (-1, -1), 1, black)
        ]))
        
        story.append(finding_table)
        story.append(Spacer(1, 0.2*inch))
        
        # Description
        story.append(Paragraph("<b>Description:</b>", styles['Heading4']))
        story.append(Paragraph(finding.description, styles['Normal']))
        story.append(Spacer(1, 0.1*inch))
        
        # Remediation
        if finding.remediation:
            story.append(Paragraph("<b>Remediation:</b>", styles['Heading4']))
            story.append(Paragraph(finding.remediation, styles['Normal']))
        
        story.append(Spacer(1, 0.3*inch))
    
    # Recommendations
    story.append(PageBreak())
    story.append(Paragraph("4. Recommendations", heading_style))
    
    recommendations_text = """
    Based on the findings identified during this penetration test, we recommend addressing vulnerabilities 
    in the following priority order:
    
    <b>1. Critical Vulnerabilities</b><br/>
    Address all critical severity vulnerabilities immediately as they pose an immediate threat to the organization.
    
    <b>2. High-Risk Vulnerabilities</b><br/>
    Remediate high-risk vulnerabilities within 30 days as they represent significant security risks.
    
    <b>3. Medium-Risk Vulnerabilities</b><br/>
    Plan remediation for medium-risk vulnerabilities within 90 days.
    
    <b>4. Low-Risk and Informational Findings</b><br/>
    Address these findings as part of regular security maintenance cycles.
    """
    
    story.append(Paragraph(recommendations_text, styles['Normal']))
    
    # Build PDF
    doc.build(story)
    buffer.seek(0)
    
    # Create filename
    filename = f"Pentest_Report_{project.name.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.pdf"
    
    return send_file(
        buffer,
        as_attachment=True,
        download_name=filename,
        mimetype='application/pdf'
    )

@reports_bp.route('/preview/pentest/<int:project_id>')
@require_auth
@require_role(['admin', 'super_admin', 'pentester', 'client'])
def preview_pentest_report(project_id):
    project = Project.query.get_or_404(project_id)
    user = User.query.get(session['user_id'])
    
    # Check access
    if user.role == 'client':
        if not UserProject.query.filter_by(user_id=user.id, project_id=project_id).first():
            flash('Access denied to this project', 'danger')
            return redirect(url_for('client.dashboard'))
    elif user.role in ['pentester']:
        if not UserProject.query.filter_by(user_id=user.id, project_id=project_id).first():
            flash('Access denied to this project', 'danger')
            return redirect(url_for('secure.dashboard'))
    
    # Get findings with statistics
    findings = Finding.query.filter_by(project_id=project_id).all()
    
    finding_stats = {
        'total': len(findings),
        'critical': len([f for f in findings if f.severity == 'critical']),
        'high': len([f for f in findings if f.severity == 'high']),
        'medium': len([f for f in findings if f.severity == 'medium']),
        'low': len([f for f in findings if f.severity == 'low']),
        'informational': len([f for f in findings if f.severity == 'informational']),
        'open': len([f for f in findings if f.status == 'open']),
        'closed': len([f for f in findings if f.status == 'closed'])
    }
    
    return render_template('reports/preview.html', project=project, 
                         findings=findings, finding_stats=finding_stats)
