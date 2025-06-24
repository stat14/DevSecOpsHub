from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from models import User, Project, Finding, UserProject
from app import db
from auth import require_auth, require_role

client_bp = Blueprint('client', __name__)

@client_bp.route('/dashboard')
@require_auth
@require_role(['client'])
def dashboard():
    user = User.query.get(session['user_id'])
    
    # Get assigned projects for client
    assigned_project_ids = [up.project_id for up in UserProject.query.filter_by(user_id=user.id).all()]
    projects = Project.query.filter(Project.id.in_(assigned_project_ids)).all()
    
    # Separate projects by type
    pentest_projects = [p for p in projects if p.project_type == 'pentest']
    dev_projects = [p for p in projects if p.project_type == 'development']
    
    return render_template('client/dashboard.html', 
                         pentest_projects=pentest_projects,
                         dev_projects=dev_projects)

@client_bp.route('/project/<int:project_id>')
@require_auth
@require_role(['client'])
def project_detail(project_id):
    project = Project.query.get_or_404(project_id)
    user = User.query.get(session['user_id'])
    
    # Check if client has access to this project
    if not UserProject.query.filter_by(user_id=user.id, project_id=project_id).first():
        flash('Access denied to this project', 'danger')
        return redirect(url_for('client.dashboard'))
    
    if project.project_type == 'pentest':
        # Get findings with statistics
        findings = Finding.query.filter_by(project_id=project_id).all()
        
        finding_stats = {
            'critical': len([f for f in findings if f.severity == 'critical']),
            'high': len([f for f in findings if f.severity == 'high']),
            'medium': len([f for f in findings if f.severity == 'medium']),
            'low': len([f for f in findings if f.severity == 'low']),
            'informational': len([f for f in findings if f.severity == 'informational']),
            'open': len([f for f in findings if f.status == 'open']),
            'closed': len([f for f in findings if f.status == 'closed'])
        }
        
        return render_template('client/project.html', project=project, 
                             findings=findings, finding_stats=finding_stats)
    
    else:  # development project
        # Get tasks organized by status
        tasks = project.tasks
        task_stats = {
            'todo': len([t for t in tasks if t.status == 'todo']),
            'in_progress': len([t for t in tasks if t.status == 'in_progress']),
            'done': len([t for t in tasks if t.status == 'done'])
        }
        
        return render_template('client/project.html', project=project, 
                             tasks=tasks, task_stats=task_stats)
