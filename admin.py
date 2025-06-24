from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from werkzeug.security import generate_password_hash
from models import User, Project, ActivityLog, UserProject, Finding, Task
from app import db
from auth import require_auth, require_role
from datetime import datetime
import logging

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/dashboard')
@require_auth
@require_role(['admin', 'super_admin'])
def dashboard():
    # Get statistics
    stats = {
        'total_users': User.query.count(),
        'total_projects': Project.query.count(),
        'active_pentest_projects': Project.query.filter_by(project_type='pentest', status='active').count(),
        'active_dev_projects': Project.query.filter_by(project_type='development', status='active').count(),
        'total_findings': Finding.query.count(),
        'critical_findings': Finding.query.filter_by(severity='critical', status='open').count(),
        'total_tasks': Task.query.count(),
        'completed_tasks': Task.query.filter_by(status='done').count()
    }
    
    # Recent activities
    recent_activities = ActivityLog.query.order_by(ActivityLog.created_at.desc()).limit(10).all()
    
    # User distribution by role
    user_roles = db.session.query(User.role, db.func.count(User.id)).group_by(User.role).all()
    
    return render_template('admin/dashboard.html', stats=stats, 
                         recent_activities=recent_activities, user_roles=user_roles)

@admin_bp.route('/users')
@require_auth
@require_role(['admin', 'super_admin'])
def users():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    role_filter = request.args.get('role', '')
    
    query = User.query
    
    if search:
        query = query.filter(
            (User.username.contains(search)) |
            (User.email.contains(search)) |
            (User.first_name.contains(search)) |
            (User.last_name.contains(search))
        )
    
    if role_filter:
        query = query.filter_by(role=role_filter)
    
    users = query.order_by(User.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    
    roles = ['super_admin', 'admin', 'pentester', 'developer', 'client']
    
    return render_template('admin/users.html', users=users, roles=roles,
                         search=search, role_filter=role_filter)

@admin_bp.route('/users/create', methods=['POST'])
@require_auth
@require_role(['admin', 'super_admin'])
def create_user():
    username = request.form['username']
    email = request.form['email']
    password = request.form['password']
    first_name = request.form['first_name']
    last_name = request.form['last_name']
    role = request.form['role']
    
    # Validation
    if User.query.filter_by(email=email).first():
        flash('Email already exists', 'danger')
        return redirect(url_for('admin.users'))
    
    if User.query.filter_by(username=username).first():
        flash('Username already exists', 'danger')
        return redirect(url_for('admin.users'))
    
    # Only super admin can create admin users
    current_user = User.query.get(session['user_id'])
    if role in ['admin', 'super_admin'] and current_user.role != 'super_admin':
        flash('Only Super Admin can create Admin users', 'danger')
        return redirect(url_for('admin.users'))
    
    user = User(
        username=username,
        email=email,
        password_hash=generate_password_hash(password),
        first_name=first_name,
        last_name=last_name,
        role=role
    )
    
    db.session.add(user)
    db.session.commit()
    
    # Log activity
    activity = ActivityLog(
        user_id=session['user_id'],
        action='create_user',
        description=f'Created user {username} with role {role}',
        entity_type='user',
        entity_id=user.id
    )
    db.session.add(activity)
    db.session.commit()
    
    flash(f'User {username} created successfully', 'success')
    return redirect(url_for('admin.users'))

@admin_bp.route('/users/<int:user_id>/edit', methods=['POST'])
@require_auth
@require_role(['admin', 'super_admin'])
def edit_user(user_id):
    user = User.query.get_or_404(user_id)
    current_user = User.query.get(session['user_id'])
    
    # Prevent editing super admin unless you are super admin
    if user.role == 'super_admin' and current_user.role != 'super_admin':
        flash('Only Super Admin can edit Super Admin users', 'danger')
        return redirect(url_for('admin.users'))
    
    user.username = request.form['username']
    user.email = request.form['email']
    user.first_name = request.form['first_name']
    user.last_name = request.form['last_name']
    
    new_role = request.form['role']
    if new_role in ['admin', 'super_admin'] and current_user.role != 'super_admin':
        flash('Only Super Admin can assign Admin roles', 'danger')
        return redirect(url_for('admin.users'))
    
    user.role = new_role
    user.is_active = 'is_active' in request.form
    
    db.session.commit()
    
    # Log activity
    activity = ActivityLog(
        user_id=session['user_id'],
        action='edit_user',
        description=f'Modified user {user.username}',
        entity_type='user',
        entity_id=user.id
    )
    db.session.add(activity)
    db.session.commit()
    
    flash(f'User {user.username} updated successfully', 'success')
    return redirect(url_for('admin.users'))

@admin_bp.route('/users/<int:user_id>/delete', methods=['POST'])
@require_auth
@require_role(['super_admin'])
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    current_user = User.query.get(session['user_id'])
    
    # Prevent deleting yourself
    if user.id == current_user.id:
        flash('You cannot delete your own account', 'danger')
        return redirect(url_for('admin.users'))
    
    username = user.username
    db.session.delete(user)
    db.session.commit()
    
    # Log activity
    activity = ActivityLog(
        user_id=session['user_id'],
        action='delete_user',
        description=f'Deleted user {username}',
        entity_type='user',
        entity_id=user_id
    )
    db.session.add(activity)
    db.session.commit()
    
    flash(f'User {username} deleted successfully', 'success')
    return redirect(url_for('admin.users'))

@admin_bp.route('/projects')
@require_auth
@require_role(['admin', 'super_admin'])
def projects():
    page = request.args.get('page', 1, type=int)
    project_type = request.args.get('type', '')
    status = request.args.get('status', '')
    
    query = Project.query
    
    if project_type:
        query = query.filter_by(project_type=project_type)
    
    if status:
        query = query.filter_by(status=status)
    
    projects = query.order_by(Project.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    
    return render_template('admin/projects.html', projects=projects,
                         project_type=project_type, status=status)

@admin_bp.route('/projects/create', methods=['POST'])
@require_auth
@require_role(['admin', 'super_admin'])
def create_project():
    name = request.form['name']
    description = request.form['description']
    client_name = request.form.get('client_name', '')
    project_type = request.form['project_type']
    
    project = Project(
        name=name,
        description=description,
        client_name=client_name,
        project_type=project_type,
        created_by=session['user_id']
    )
    
    db.session.add(project)
    db.session.commit()
    
    # Log activity
    activity = ActivityLog(
        user_id=session['user_id'],
        action='create_project',
        description=f'Created {project_type} project: {name}',
        entity_type='project',
        entity_id=project.id
    )
    db.session.add(activity)
    db.session.commit()
    
    flash(f'Project {name} created successfully', 'success')
    return redirect(url_for('admin.projects'))

@admin_bp.route('/projects/<int:project_id>/assign', methods=['POST'])
@require_auth
@require_role(['admin', 'super_admin'])
def assign_project(project_id):
    project = Project.query.get_or_404(project_id)
    user_ids = request.form.getlist('user_ids')
    
    # Remove existing assignments
    UserProject.query.filter_by(project_id=project_id).delete()
    
    # Add new assignments
    for user_id in user_ids:
        assignment = UserProject(
            user_id=int(user_id),
            project_id=project_id,
            role_in_project='member'
        )
        db.session.add(assignment)
    
    db.session.commit()
    
    # Log activity
    activity = ActivityLog(
        user_id=session['user_id'],
        action='assign_project',
        description=f'Assigned {len(user_ids)} users to project {project.name}',
        entity_type='project',
        entity_id=project.id
    )
    db.session.add(activity)
    db.session.commit()
    
    flash(f'Project assignments updated for {project.name}', 'success')
    return redirect(url_for('admin.projects'))

@admin_bp.route('/nexus-secure')
@require_auth
@require_role(['admin', 'super_admin'])
def nexus_secure():
    return redirect(url_for('secure.dashboard'))

@admin_bp.route('/nexus-flow')
@require_auth
@require_role(['admin', 'super_admin'])
def nexus_flow():
    return redirect(url_for('flow.dashboard'))
