from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from models import User, Project, Finding, ActivityLog, UserProject
from app import db
from auth import require_auth, require_role
from datetime import datetime
import json

secure_bp = Blueprint('secure', __name__)

@secure_bp.route('/dashboard')
@require_auth
@require_role(['admin', 'super_admin', 'pentester'])
def dashboard():
    user = User.query.get(session['user_id'])
    
    # Get projects based on user role
    if user.role in ['admin', 'super_admin']:
        projects = Project.query.filter_by(project_type='pentest').all()
    else:
        # Get assigned projects for pentester
        assigned_project_ids = [up.project_id for up in UserProject.query.filter_by(user_id=user.id).all()]
        projects = Project.query.filter(
            Project.id.in_(assigned_project_ids),
            Project.project_type == 'pentest'
        ).all()
    
    # Get statistics
    stats = {
        'total_projects': len(projects),
        'active_projects': len([p for p in projects if p.status == 'active']),
        'total_findings': sum([len(p.findings) for p in projects]),
        'critical_findings': sum([len([f for f in p.findings if f.severity == 'critical' and f.status == 'open']) for p in projects])
    }
    
    return render_template('secure/dashboard.html', projects=projects, stats=stats)

@secure_bp.route('/project/<int:project_id>')
@require_auth
@require_role(['admin', 'super_admin', 'pentester'])
def project_detail(project_id):
    project = Project.query.get_or_404(project_id)
    
    # Check access
    user = User.query.get(session['user_id'])
    if user.role not in ['admin', 'super_admin']:
        if not UserProject.query.filter_by(user_id=user.id, project_id=project_id).first():
            flash('Access denied to this project', 'danger')
            return redirect(url_for('secure.dashboard'))
    
    # Get findings with filters
    severity_filter = request.args.get('severity', '')
    status_filter = request.args.get('status', '')
    sort_by = request.args.get('sort', 'created_at')
    
    findings_query = Finding.query.filter_by(project_id=project_id)
    
    if severity_filter:
        findings_query = findings_query.filter_by(severity=severity_filter)
    
    if status_filter:
        findings_query = findings_query.filter_by(status=status_filter)
    
    # Apply sorting
    if sort_by == 'severity':
        severity_order = {'critical': 0, 'high': 1, 'medium': 2, 'low': 3, 'informational': 4}
        findings = sorted(findings_query.all(), key=lambda f: severity_order.get(f.severity, 5))
    elif sort_by == 'created_at':
        findings = findings_query.order_by(Finding.created_at.desc()).all()
    else:
        findings = findings_query.all()
    
    # Get finding statistics
    finding_stats = {
        'critical': len([f for f in project.findings if f.severity == 'critical']),
        'high': len([f for f in project.findings if f.severity == 'high']),
        'medium': len([f for f in project.findings if f.severity == 'medium']),
        'low': len([f for f in project.findings if f.severity == 'low']),
        'informational': len([f for f in project.findings if f.severity == 'informational']),
        'open': len([f for f in project.findings if f.status == 'open']),
        'closed': len([f for f in project.findings if f.status == 'closed'])
    }
    
    return render_template('secure/project.html', project=project, findings=findings,
                         finding_stats=finding_stats, severity_filter=severity_filter,
                         status_filter=status_filter, sort_by=sort_by)

@secure_bp.route('/project/create', methods=['POST'])
@require_auth
@require_role(['admin', 'super_admin', 'pentester'])
def create_project():
    name = request.form['name']
    description = request.form['description']
    client_name = request.form.get('client_name', '')
    
    project = Project(
        name=name,
        description=description,
        client_name=client_name,
        project_type='pentest',
        created_by=session['user_id']
    )
    
    db.session.add(project)
    db.session.flush()  # Get the ID
    
    # Auto-assign the creator to the project
    assignment = UserProject(
        user_id=session['user_id'],
        project_id=project.id,
        role_in_project='lead'
    )
    db.session.add(assignment)
    db.session.commit()
    
    # Log activity
    activity = ActivityLog(
        user_id=session['user_id'],
        action='create_pentest_project',
        description=f'Created penetration testing project: {name}',
        entity_type='project',
        entity_id=project.id
    )
    db.session.add(activity)
    db.session.commit()
    
    flash(f'Project {name} created successfully', 'success')
    return redirect(url_for('secure.project_detail', project_id=project.id))

@secure_bp.route('/finding/create', methods=['POST'])
@require_auth
@require_role(['admin', 'super_admin', 'pentester'])
def create_finding():
    project_id = request.form['project_id']
    title = request.form['title']
    description = request.form['description']
    severity = request.form['severity']
    remediation = request.form.get('remediation', '')
    cvss_score = request.form.get('cvss_score', type=float)
    cwe_id = request.form.get('cwe_id', '')
    affected_url = request.form.get('affected_url', '')
    
    # Check access
    project = Project.query.get_or_404(project_id)
    user = User.query.get(session['user_id'])
    if user.role not in ['admin', 'super_admin']:
        if not UserProject.query.filter_by(user_id=user.id, project_id=project_id).first():
            flash('Access denied to this project', 'danger')
            return redirect(url_for('secure.dashboard'))
    
    finding = Finding(
        title=title,
        description=description,
        remediation=remediation,
        severity=severity,
        cvss_score=cvss_score,
        cwe_id=cwe_id,
        affected_url=affected_url,
        project_id=project_id,
        created_by=session['user_id']
    )
    
    db.session.add(finding)
    db.session.commit()
    
    # Log activity
    activity = ActivityLog(
        user_id=session['user_id'],
        action='create_finding',
        description=f'Added {severity} finding: {title} to project {project.name}',
        entity_type='finding',
        entity_id=finding.id
    )
    db.session.add(activity)
    db.session.commit()
    
    flash(f'Finding "{title}" added successfully', 'success')
    return redirect(url_for('secure.project_detail', project_id=project_id))

@secure_bp.route('/finding/<int:finding_id>/edit', methods=['POST'])
@require_auth
@require_role(['admin', 'super_admin', 'pentester'])
def edit_finding(finding_id):
    finding = Finding.query.get_or_404(finding_id)
    
    # Check access
    user = User.query.get(session['user_id'])
    if user.role not in ['admin', 'super_admin']:
        if not UserProject.query.filter_by(user_id=user.id, project_id=finding.project_id).first():
            flash('Access denied to this finding', 'danger')
            return redirect(url_for('secure.dashboard'))
    
    finding.title = request.form['title']
    finding.description = request.form['description']
    finding.remediation = request.form.get('remediation', '')
    finding.severity = request.form['severity']
    finding.status = request.form['status']
    finding.cvss_score = request.form.get('cvss_score', type=float)
    finding.cwe_id = request.form.get('cwe_id', '')
    finding.affected_url = request.form.get('affected_url', '')
    finding.updated_at = datetime.utcnow()
    
    db.session.commit()
    
    # Log activity
    activity = ActivityLog(
        user_id=session['user_id'],
        action='edit_finding',
        description=f'Modified finding: {finding.title}',
        entity_type='finding',
        entity_id=finding.id
    )
    db.session.add(activity)
    db.session.commit()
    
    return jsonify({'success': True})

@secure_bp.route('/finding/<int:finding_id>/delete', methods=['POST'])
@require_auth
@require_role(['admin', 'super_admin', 'pentester'])
def delete_finding(finding_id):
    finding = Finding.query.get_or_404(finding_id)
    
    # Check access
    user = User.query.get(session['user_id'])
    if user.role not in ['admin', 'super_admin']:
        if not UserProject.query.filter_by(user_id=user.id, project_id=finding.project_id).first():
            flash('Access denied to this finding', 'danger')
            return redirect(url_for('secure.dashboard'))
    
    project_id = finding.project_id
    title = finding.title
    
    db.session.delete(finding)
    db.session.commit()
    
    # Log activity
    activity = ActivityLog(
        user_id=session['user_id'],
        action='delete_finding',
        description=f'Deleted finding: {title}',
        entity_type='finding',
        entity_id=finding_id
    )
    db.session.add(activity)
    db.session.commit()
    
    flash(f'Finding "{title}" deleted successfully', 'success')
    return redirect(url_for('secure.project_detail', project_id=project_id))

@secure_bp.route('/api/finding/<int:finding_id>')
@require_auth
@require_role(['admin', 'super_admin', 'pentester'])
def get_finding(finding_id):
    finding = Finding.query.get_or_404(finding_id)
    
    # Check access
    user = User.query.get(session['user_id'])
    if user.role not in ['admin', 'super_admin']:
        if not UserProject.query.filter_by(user_id=user.id, project_id=finding.project_id).first():
            return jsonify({'error': 'Access denied'}), 403
    
    return jsonify({
        'id': finding.id,
        'title': finding.title,
        'description': finding.description,
        'remediation': finding.remediation,
        'severity': finding.severity,
        'status': finding.status,
        'cvss_score': finding.cvss_score,
        'cwe_id': finding.cwe_id,
        'affected_url': finding.affected_url,
        'created_at': finding.created_at.isoformat(),
        'updated_at': finding.updated_at.isoformat()
    })
