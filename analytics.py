"""
Advanced analytics and reporting module
"""
from flask import Blueprint, render_template, jsonify, request, session
from models import User, Project, Finding, Task, ActivityLog, db
from auth import require_role
import plotly.graph_objs as go
import plotly.utils
import pandas as pd
from datetime import datetime, timedelta
from sqlalchemy import func, and_, or_
import json

analytics_bp = Blueprint('analytics', __name__)

@analytics_bp.route('/dashboard')
@role_required(['admin', 'super_admin'])
def analytics_dashboard():
    """Main analytics dashboard"""
    return render_template('analytics/dashboard.html')

@analytics_bp.route('/api/security-metrics')
@require_role(['admin', 'super_admin', 'pentester'])
def security_metrics():
    """Get security metrics data"""
    
    # Findings by severity over time
    findings_data = db.session.query(
        Finding.severity,
        func.date(Finding.created_at).label('date'),
        func.count(Finding.id).label('count')
    ).group_by(Finding.severity, func.date(Finding.created_at)).all()
    
    # Prepare data for charts
    severity_trend = {}
    for finding in findings_data:
        if finding.severity not in severity_trend:
            severity_trend[finding.severity] = {'dates': [], 'counts': []}
        severity_trend[finding.severity]['dates'].append(str(finding.date))
        severity_trend[finding.severity]['counts'].append(finding.count)
    
    # Top vulnerabilities
    top_vulns = db.session.query(
        Finding.title,
        func.count(Finding.id).label('count')
    ).group_by(Finding.title).order_by(func.count(Finding.id).desc()).limit(10).all()
    
    # Project risk scores
    project_risks = db.session.query(
        Project.name,
        func.count(Finding.id).label('total_findings'),
        func.sum(
            func.case(
                (Finding.severity == 'critical', 10),
                (Finding.severity == 'high', 7),
                (Finding.severity == 'medium', 4),
                (Finding.severity == 'low', 1),
                else_=0
            )
        ).label('risk_score')
    ).join(Finding, Project.id == Finding.project_id, isouter=True)\
     .group_by(Project.id, Project.name).all()
    
    return jsonify({
        'severity_trend': severity_trend,
        'top_vulnerabilities': [{'name': v.title, 'count': v.count} for v in top_vulns],
        'project_risks': [{'name': p.name, 'findings': p.total_findings or 0, 'score': float(p.risk_score or 0)} for p in project_risks]
    })

@analytics_bp.route('/api/development-metrics')
@require_role(['admin', 'super_admin', 'developer'])
def development_metrics():
    """Get development metrics data"""
    
    # Task completion trends
    task_data = db.session.query(
        Task.status,
        func.date(Task.updated_at).label('date'),
        func.count(Task.id).label('count')
    ).group_by(Task.status, func.date(Task.updated_at)).all()
    
    # Team productivity
    user_productivity = db.session.query(
        User.username,
        func.count(Task.id).label('tasks_completed')
    ).join(Task, User.id == Task.assigned_to, isouter=True)\
     .filter(Task.status == 'completed')\
     .group_by(User.id, User.username).all()
    
    # Sprint velocity (tasks completed per week)
    end_date = datetime.now()
    start_date = end_date - timedelta(weeks=12)
    
    weekly_velocity = db.session.query(
        func.date_trunc('week', Task.updated_at).label('week'),
        func.count(Task.id).label('completed_tasks')
    ).filter(
        and_(
            Task.status == 'completed',
            Task.updated_at >= start_date,
            Task.updated_at <= end_date
        )
    ).group_by(func.date_trunc('week', Task.updated_at)).all()
    
    return jsonify({
        'task_trends': [{'status': t.status, 'date': str(t.date), 'count': t.count} for t in task_data],
        'team_productivity': [{'user': u.username, 'tasks': u.tasks_completed or 0} for u in user_productivity],
        'sprint_velocity': [{'week': str(v.week), 'tasks': v.completed_tasks} for v in weekly_velocity]
    })

@analytics_bp.route('/api/user-activity')
@require_role(['admin', 'super_admin'])
def user_activity():
    """Get user activity analytics"""
    
    # Daily active users
    daily_activity = db.session.query(
        func.date(ActivityLog.timestamp).label('date'),
        func.count(func.distinct(ActivityLog.user_id)).label('active_users')
    ).group_by(func.date(ActivityLog.timestamp)).order_by(func.date(ActivityLog.timestamp)).all()
    
    # Most active users
    top_users = db.session.query(
        User.username,
        func.count(ActivityLog.id).label('activity_count')
    ).join(ActivityLog, User.id == ActivityLog.user_id)\
     .group_by(User.id, User.username)\
     .order_by(func.count(ActivityLog.id).desc()).limit(10).all()
    
    # Activity by type
    activity_types = db.session.query(
        ActivityLog.action,
        func.count(ActivityLog.id).label('count')
    ).group_by(ActivityLog.action).all()
    
    return jsonify({
        'daily_activity': [{'date': str(a.date), 'users': a.active_users} for a in daily_activity],
        'top_users': [{'user': u.username, 'activities': u.activity_count} for u in top_users],
        'activity_types': [{'action': a.action, 'count': a.count} for a in activity_types]
    })

@analytics_bp.route('/api/project-overview')
@require_role(['admin', 'super_admin'])
def project_overview():
    """Get project overview analytics"""
    
    # Project status distribution
    project_status = db.session.query(
        Project.status,
        func.count(Project.id).label('count')
    ).group_by(Project.status).all()
    
    # Projects by type
    project_types = db.session.query(
        Project.project_type,
        func.count(Project.id).label('count')
    ).group_by(Project.project_type).all()
    
    # Average project duration
    completed_projects = db.session.query(
        Project.name,
        Project.start_date,
        Project.end_date,
        func.extract('days', Project.end_date - Project.start_date).label('duration')
    ).filter(Project.status == 'completed', Project.end_date.isnot(None)).all()
    
    return jsonify({
        'status_distribution': [{'status': p.status, 'count': p.count} for p in project_status],
        'type_distribution': [{'type': p.project_type, 'count': p.count} for p in project_types],
        'completed_projects': [{'name': p.name, 'duration': float(p.duration or 0)} for p in completed_projects]
    })

def generate_advanced_chart(chart_type, data, title="Chart", x_label="X", y_label="Y"):
    """Generate advanced Plotly charts"""
    
    if chart_type == 'line':
        fig = go.Figure()
        for series_name, series_data in data.items():
            fig.add_trace(go.Scatter(
                x=series_data['x'],
                y=series_data['y'],
                mode='lines+markers',
                name=series_name,
                line=dict(width=3),
                marker=dict(size=8)
            ))
    
    elif chart_type == 'bar':
        fig = go.Figure()
        for series_name, series_data in data.items():
            fig.add_trace(go.Bar(
                x=series_data['x'],
                y=series_data['y'],
                name=series_name
            ))
    
    elif chart_type == 'pie':
        fig = go.Figure(data=[go.Pie(
            labels=data['labels'],
            values=data['values'],
            hole=0.3,
            textinfo='label+percent'
        )])
    
    elif chart_type == 'heatmap':
        fig = go.Figure(data=go.Heatmap(
            z=data['z'],
            x=data['x'],
            y=data['y'],
            colorscale='RdYlBu_r'
        ))
    
    else:
        return None
    
    fig.update_layout(
        title=title,
        xaxis_title=x_label,
        yaxis_title=y_label,
        template='plotly_white',
        font=dict(size=12),
        showlegend=True
    )
    
    return json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

@analytics_bp.route('/api/custom-report')
@require_role(['admin', 'super_admin'])
def custom_report():
    """Generate custom analytics report"""
    
    report_type = request.args.get('type', 'summary')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    filters = {}
    if start_date:
        filters['start_date'] = datetime.fromisoformat(start_date)
    if end_date:
        filters['end_date'] = datetime.fromisoformat(end_date)
    
    if report_type == 'security':
        return jsonify(generate_security_report(filters))
    elif report_type == 'productivity':
        return jsonify(generate_productivity_report(filters))
    elif report_type == 'user_engagement':
        return jsonify(generate_user_engagement_report(filters))
    else:
        return jsonify(generate_summary_report(filters))

def generate_security_report(filters):
    """Generate detailed security report"""
    query = db.session.query(Finding)
    
    if 'start_date' in filters:
        query = query.filter(Finding.created_at >= filters['start_date'])
    if 'end_date' in filters:
        query = query.filter(Finding.created_at <= filters['end_date'])
    
    findings = query.all()
    
    return {
        'total_findings': len(findings),
        'by_severity': {
            severity: len([f for f in findings if f.severity == severity])
            for severity in ['critical', 'high', 'medium', 'low', 'informational']
        },
        'by_status': {
            status: len([f for f in findings if f.status == status])
            for status in ['open', 'in_progress', 'closed', 'false_positive']
        },
        'avg_resolution_time': calculate_avg_resolution_time(findings)
    }

def generate_productivity_report(filters):
    """Generate productivity report"""
    query = db.session.query(Task)
    
    if 'start_date' in filters:
        query = query.filter(Task.created_at >= filters['start_date'])
    if 'end_date' in filters:
        query = query.filter(Task.created_at <= filters['end_date'])
    
    tasks = query.all()
    
    return {
        'total_tasks': len(tasks),
        'completed_tasks': len([t for t in tasks if t.status == 'completed']),
        'completion_rate': len([t for t in tasks if t.status == 'completed']) / len(tasks) * 100 if tasks else 0,
        'by_priority': {
            priority: len([t for t in tasks if t.priority == priority])
            for priority in ['low', 'medium', 'high', 'urgent']
        }
    }

def generate_user_engagement_report(filters):
    """Generate user engagement report"""
    query = db.session.query(ActivityLog)
    
    if 'start_date' in filters:
        query = query.filter(ActivityLog.timestamp >= filters['start_date'])
    if 'end_date' in filters:
        query = query.filter(ActivityLog.timestamp <= filters['end_date'])
    
    activities = query.all()
    
    return {
        'total_activities': len(activities),
        'unique_users': len(set(a.user_id for a in activities)),
        'avg_activities_per_user': len(activities) / len(set(a.user_id for a in activities)) if activities else 0,
        'most_active_day': get_most_active_day(activities)
    }

def generate_summary_report(filters):
    """Generate summary report"""
    return {
        'security': generate_security_report(filters),
        'productivity': generate_productivity_report(filters),
        'user_engagement': generate_user_engagement_report(filters)
    }

def calculate_avg_resolution_time(findings):
    """Calculate average resolution time for findings"""
    resolved_findings = [f for f in findings if f.status == 'closed' and f.updated_at]
    if not resolved_findings:
        return 0
    
    total_time = sum(
        (f.updated_at - f.created_at).total_seconds() / 3600  # hours
        for f in resolved_findings
    )
    
    return total_time / len(resolved_findings)

def get_most_active_day(activities):
    """Get the most active day from activities"""
    if not activities:
        return None
    
    day_counts = {}
    for activity in activities:
        day = activity.timestamp.strftime('%A')
        day_counts[day] = day_counts.get(day, 0) + 1
    
    return max(day_counts.items(), key=lambda x: x[1])[0] if day_counts else None