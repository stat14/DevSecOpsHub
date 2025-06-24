from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from models import User, Project, Task, TaskComment, ActivityLog, UserProject
from app import db
from auth import require_auth, require_role
from datetime import datetime
import json

flow_bp = Blueprint('flow', __name__)

@flow_bp.route('/dashboard')
@require_auth
@require_role(['admin', 'super_admin', 'developer'])
def dashboard():
    user = User.query.get(session['user_id'])
    
    # Get projects based on user role
    if user.role in ['admin', 'super_admin']:
        projects = Project.query.filter_by(project_type='development').all()
    else:
        # Get assigned projects for developer
        assigned_project_ids = [up.project_id for up in UserProject.query.filter_by(user_id=user.id).all()]
        projects = Project.query.filter(
            Project.id.in_(assigned_project_ids),
            Project.project_type == 'development'
        ).all()
    
    # Get statistics
    stats = {
        'total_projects': len(projects),
        'active_projects': len([p for p in projects if p.status == 'active']),
        'total_tasks': sum([len(p.tasks) for p in projects]),
        'completed_tasks': sum([len([t for t in p.tasks if t.status == 'done']) for p in projects])
    }
    
    return render_template('flow/dashboard.html', projects=projects, stats=stats)

@flow_bp.route('/board/<int:project_id>')
@require_auth
@require_role(['admin', 'super_admin', 'developer'])
def board(project_id):
    project = Project.query.get_or_404(project_id)
    
    # Check access
    user = User.query.get(session['user_id'])
    if user.role not in ['admin', 'super_admin']:
        if not UserProject.query.filter_by(user_id=user.id, project_id=project_id).first():
            flash('Access denied to this project', 'danger')
            return redirect(url_for('flow.dashboard'))
    
    # Get tasks organized by status
    todo_tasks = Task.query.filter_by(project_id=project_id, status='todo').order_by(Task.position).all()
    in_progress_tasks = Task.query.filter_by(project_id=project_id, status='in_progress').order_by(Task.position).all()
    done_tasks = Task.query.filter_by(project_id=project_id, status='done').order_by(Task.position).all()
    
    # Get project team members
    team_members = User.query.join(UserProject).filter(UserProject.project_id == project_id).all()
    
    tasks_by_status = {
        'todo': todo_tasks,
        'in_progress': in_progress_tasks,
        'done': done_tasks
    }
    
    return render_template('flow/board.html', project=project, tasks_by_status=tasks_by_status,
                         team_members=team_members)

@flow_bp.route('/project/create', methods=['POST'])
@require_auth
@require_role(['admin', 'super_admin', 'developer'])
def create_project():
    name = request.form['name']
    description = request.form['description']
    
    project = Project(
        name=name,
        description=description,
        project_type='development',
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
        action='create_dev_project',
        description=f'Created development project: {name}',
        entity_type='project',
        entity_id=project.id
    )
    db.session.add(activity)
    db.session.commit()
    
    flash(f'Project {name} created successfully', 'success')
    return redirect(url_for('flow.board', project_id=project.id))

@flow_bp.route('/task/create', methods=['POST'])
@require_auth
@require_role(['admin', 'super_admin', 'developer'])
def create_task():
    project_id = request.form['project_id']
    title = request.form['title']
    description = request.form.get('description', '')
    status = request.form.get('status', 'todo')
    priority = request.form.get('priority', 'medium')
    assigned_to = request.form.get('assigned_to', type=int)
    labels = request.form.get('labels', '')
    
    # Check access
    project = Project.query.get_or_404(project_id)
    user = User.query.get(session['user_id'])
    if user.role not in ['admin', 'super_admin']:
        if not UserProject.query.filter_by(user_id=user.id, project_id=project_id).first():
            flash('Access denied to this project', 'danger')
            return redirect(url_for('flow.dashboard'))
    
    # Get next position for the status column
    max_position = db.session.query(db.func.max(Task.position)).filter_by(
        project_id=project_id, status=status
    ).scalar() or 0
    
    task = Task(
        title=title,
        description=description,
        status=status,
        priority=priority,
        labels=labels,
        position=max_position + 1,
        project_id=project_id,
        created_by=session['user_id'],
        assigned_to=assigned_to if assigned_to else None
    )
    
    db.session.add(task)
    db.session.commit()
    
    # Log activity
    activity = ActivityLog(
        user_id=session['user_id'],
        action='create_task',
        description=f'Created task: {title} in project {project.name}',
        entity_type='task',
        entity_id=task.id
    )
    db.session.add(activity)
    db.session.commit()
    
    if request.headers.get('Content-Type') == 'application/json':
        return jsonify({'success': True, 'task_id': task.id})
    
    flash(f'Task "{title}" created successfully', 'success')
    return redirect(url_for('flow.board', project_id=project_id))

@flow_bp.route('/task/<int:task_id>/edit', methods=['POST'])
@require_auth
@require_role(['admin', 'super_admin', 'developer'])
def edit_task(task_id):
    task = Task.query.get_or_404(task_id)
    
    # Check access
    user = User.query.get(session['user_id'])
    if user.role not in ['admin', 'super_admin']:
        if not UserProject.query.filter_by(user_id=user.id, project_id=task.project_id).first():
            return jsonify({'error': 'Access denied'}), 403
    
    task.title = request.form['title']
    task.description = request.form.get('description', '')
    task.priority = request.form.get('priority', 'medium')
    task.labels = request.form.get('labels', '')
    
    assigned_to = request.form.get('assigned_to', type=int)
    task.assigned_to = assigned_to if assigned_to else None
    
    task.updated_at = datetime.utcnow()
    
    db.session.commit()
    
    # Log activity
    activity = ActivityLog(
        user_id=session['user_id'],
        action='edit_task',
        description=f'Modified task: {task.title}',
        entity_type='task',
        entity_id=task.id
    )
    db.session.add(activity)
    db.session.commit()
    
    return jsonify({'success': True})

@flow_bp.route('/task/<int:task_id>/move', methods=['POST'])
@require_auth
@require_role(['admin', 'super_admin', 'developer'])
def move_task(task_id):
    task = Task.query.get_or_404(task_id)
    
    # Check access
    user = User.query.get(session['user_id'])
    if user.role not in ['admin', 'super_admin']:
        if not UserProject.query.filter_by(user_id=user.id, project_id=task.project_id).first():
            return jsonify({'error': 'Access denied'}), 403
    
    new_status = request.json.get('status')
    new_position = request.json.get('position', 0)
    
    old_status = task.status
    
    # Update positions for affected tasks
    if old_status == new_status:
        # Moving within same column
        if new_position > task.position:
            # Moving down - decrease position of tasks in between
            Task.query.filter(
                Task.project_id == task.project_id,
                Task.status == new_status,
                Task.position > task.position,
                Task.position <= new_position
            ).update({'position': Task.position - 1})
        else:
            # Moving up - increase position of tasks in between
            Task.query.filter(
                Task.project_id == task.project_id,
                Task.status == new_status,
                Task.position >= new_position,
                Task.position < task.position
            ).update({'position': Task.position + 1})
    else:
        # Moving to different column
        # Decrease position of tasks after old position in old column
        Task.query.filter(
            Task.project_id == task.project_id,
            Task.status == old_status,
            Task.position > task.position
        ).update({'position': Task.position - 1})
        
        # Increase position of tasks at or after new position in new column
        Task.query.filter(
            Task.project_id == task.project_id,
            Task.status == new_status,
            Task.position >= new_position
        ).update({'position': Task.position + 1})
    
    # Update the task
    task.status = new_status
    task.position = new_position
    task.updated_at = datetime.utcnow()
    
    db.session.commit()
    
    # Log activity
    activity = ActivityLog(
        user_id=session['user_id'],
        action='move_task',
        description=f'Moved task "{task.title}" to {new_status}',
        entity_type='task',
        entity_id=task.id
    )
    db.session.add(activity)
    db.session.commit()
    
    return jsonify({'success': True})

@flow_bp.route('/task/<int:task_id>/delete', methods=['POST'])
@require_auth
@require_role(['admin', 'super_admin', 'developer'])
def delete_task(task_id):
    task = Task.query.get_or_404(task_id)
    
    # Check access
    user = User.query.get(session['user_id'])
    if user.role not in ['admin', 'super_admin']:
        if not UserProject.query.filter_by(user_id=user.id, project_id=task.project_id).first():
            flash('Access denied to this task', 'danger')
            return redirect(url_for('flow.dashboard'))
    
    project_id = task.project_id
    title = task.title
    
    db.session.delete(task)
    db.session.commit()
    
    # Log activity
    activity = ActivityLog(
        user_id=session['user_id'],
        action='delete_task',
        description=f'Deleted task: {title}',
        entity_type='task',
        entity_id=task_id
    )
    db.session.add(activity)
    db.session.commit()
    
    flash(f'Task "{title}" deleted successfully', 'success')
    return redirect(url_for('flow.board', project_id=project_id))

@flow_bp.route('/api/task/<int:task_id>')
@require_auth
@require_role(['admin', 'super_admin', 'developer'])
def get_task(task_id):
    task = Task.query.get_or_404(task_id)
    
    # Check access
    user = User.query.get(session['user_id'])
    if user.role not in ['admin', 'super_admin']:
        if not UserProject.query.filter_by(user_id=user.id, project_id=task.project_id).first():
            return jsonify({'error': 'Access denied'}), 403
    
    # Get comments
    comments = []
    for comment in task.comments:
        comments.append({
            'id': comment.id,
            'content': comment.content,
            'created_at': comment.created_at.isoformat(),
            'user': {
                'name': comment.user.full_name,
                'username': comment.user.username
            }
        })
    
    return jsonify({
        'id': task.id,
        'title': task.title,
        'description': task.description,
        'status': task.status,
        'priority': task.priority,
        'labels': task.labels,
        'assigned_to': task.assigned_to,
        'assigned_user': task.assigned_user.full_name if task.assigned_user else None,
        'created_at': task.created_at.isoformat(),
        'updated_at': task.updated_at.isoformat(),
        'comments': comments
    })

@flow_bp.route('/task/<int:task_id>/comment', methods=['POST'])
@require_auth
@require_role(['admin', 'super_admin', 'developer'])
def add_comment(task_id):
    task = Task.query.get_or_404(task_id)
    content = request.form['content']
    
    # Check access
    user = User.query.get(session['user_id'])
    if user.role not in ['admin', 'super_admin']:
        if not UserProject.query.filter_by(user_id=user.id, project_id=task.project_id).first():
            return jsonify({'error': 'Access denied'}), 403
    
    comment = TaskComment(
        content=content,
        task_id=task_id,
        user_id=session['user_id']
    )
    
    db.session.add(comment)
    db.session.commit()
    
    # Log activity
    activity = ActivityLog(
        user_id=session['user_id'],
        action='add_comment',
        description=f'Added comment to task: {task.title}',
        entity_type='task',
        entity_id=task.id
    )
    db.session.add(activity)
    db.session.commit()
    
    return jsonify({'success': True})
