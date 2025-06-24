"""
Enhanced Role-Based Access Control (RBAC) system
"""
from functools import wraps
from flask import session, request, jsonify, abort
from models import User, UserProject, Project
import json

# Permission definitions
PERMISSIONS = {
    'super_admin': {
        'admin': ['*'],  # All admin permissions
        'secure': ['*'],  # All security permissions
        'flow': ['*'],    # All development permissions
        'client': ['*'],  # All client permissions
        'analytics': ['*'], # All analytics permissions
        'reports': ['*']   # All reports permissions
    },
    'admin': {
        'admin': ['view_users', 'create_user', 'edit_user', 'delete_user', 'view_projects', 'create_project', 'edit_project', 'assign_users'],
        'secure': ['view_all_projects', 'view_findings', 'create_finding', 'edit_finding'],
        'flow': ['view_all_projects', 'view_tasks', 'create_task', 'edit_task'],
        'client': ['view_assigned_projects'],
        'analytics': ['view_all_analytics', 'export_reports'],
        'reports': ['generate_reports', 'view_reports']
    },
    'pentester': {
        'secure': ['view_assigned_projects', 'view_findings', 'create_finding', 'edit_finding', 'delete_finding'],
        'reports': ['generate_security_reports', 'view_security_reports'],
        'analytics': ['view_security_analytics']
    },
    'developer': {
        'flow': ['view_assigned_projects', 'view_tasks', 'create_task', 'edit_task', 'update_task_status'],
        'analytics': ['view_development_analytics']
    },
    'client': {
        'client': ['view_assigned_projects', 'view_project_status'],
        'reports': ['view_client_reports']
    }
}

# Resource-level permissions
RESOURCE_PERMISSIONS = {
    'project': {
        'view': ['super_admin', 'admin', 'pentester', 'developer', 'client'],
        'edit': ['super_admin', 'admin'],
        'delete': ['super_admin'],
        'assign_users': ['super_admin', 'admin']
    },
    'finding': {
        'view': ['super_admin', 'admin', 'pentester', 'client'],
        'create': ['super_admin', 'admin', 'pentester'],
        'edit': ['super_admin', 'admin', 'pentester'],
        'delete': ['super_admin', 'admin', 'pentester']
    },
    'task': {
        'view': ['super_admin', 'admin', 'developer'],
        'create': ['super_admin', 'admin', 'developer'],
        'edit': ['super_admin', 'admin', 'developer'],
        'delete': ['super_admin', 'admin']
    },
    'user': {
        'view': ['super_admin', 'admin'],
        'create': ['super_admin', 'admin'],
        'edit': ['super_admin', 'admin'],
        'delete': ['super_admin']
    }
}

def has_permission(user_role, module, action):
    """Check if user role has permission for specific module and action"""
    if user_role not in PERMISSIONS:
        return False
    
    module_perms = PERMISSIONS[user_role].get(module, [])
    return '*' in module_perms or action in module_perms

def has_resource_permission(user_role, resource_type, action, resource_id=None, user_id=None):
    """Check if user has permission to perform action on specific resource"""
    if user_role not in RESOURCE_PERMISSIONS.get(resource_type, {}):
        return False
    
    allowed_roles = RESOURCE_PERMISSIONS[resource_type].get(action, [])
    if user_role not in allowed_roles:
        return False
    
    # Additional checks for resource-specific access
    if resource_id and user_id:
        return check_resource_access(user_role, resource_type, resource_id, user_id)
    
    return True

def check_resource_access(user_role, resource_type, resource_id, user_id):
    """Check if user has access to specific resource"""
    if user_role in ['super_admin', 'admin']:
        return True
    
    if resource_type == 'project':
        # Check if user is assigned to project
        user_project = UserProject.query.filter_by(
            user_id=user_id, 
            project_id=resource_id
        ).first()
        return user_project is not None
    
    elif resource_type in ['finding', 'task']:
        # Check through project assignment
        if resource_type == 'finding':
            from models import Finding
            resource = Finding.query.get(resource_id)
        else:
            from models import Task
            resource = Task.query.get(resource_id)
        
        if resource:
            return check_resource_access(user_role, 'project', resource.project_id, user_id)
    
    return False

def require_permission(module, action):
    """Decorator to require specific permission"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                if request.is_json:
                    return jsonify({'error': 'Authentication required'}), 401
                abort(401)
            
            user = User.query.get(session['user_id'])
            if not user or not has_permission(user.role, module, action):
                if request.is_json:
                    return jsonify({'error': 'Permission denied'}), 403
                abort(403)
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def require_resource_permission(resource_type, action):
    """Decorator to require permission on specific resource"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                if request.is_json:
                    return jsonify({'error': 'Authentication required'}), 401
                abort(401)
            
            user = User.query.get(session['user_id'])
            if not user:
                if request.is_json:
                    return jsonify({'error': 'User not found'}), 404
                abort(404)
            
            # Extract resource_id from kwargs or args
            resource_id = kwargs.get('id') or kwargs.get(f'{resource_type}_id')
            if not resource_id and args:
                resource_id = args[0] if len(args) > 0 else None
            
            if not has_resource_permission(user.role, resource_type, action, resource_id, user.id):
                if request.is_json:
                    return jsonify({'error': 'Access denied to this resource'}), 403
                abort(403)
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def get_user_permissions(user_role):
    """Get all permissions for a user role"""
    return PERMISSIONS.get(user_role, {})

def get_accessible_projects(user_id, user_role):
    """Get list of projects accessible to user"""
    if user_role in ['super_admin', 'admin']:
        return Project.query.all()
    else:
        user_projects = UserProject.query.filter_by(user_id=user_id).all()
        project_ids = [up.project_id for up in user_projects]
        return Project.query.filter(Project.id.in_(project_ids)).all() if project_ids else []

def filter_data_by_access(data, user_id, user_role, resource_type):
    """Filter data based on user access permissions"""
    if user_role in ['super_admin', 'admin']:
        return data
    
    accessible_projects = get_accessible_projects(user_id, user_role)
    accessible_project_ids = [p.id for p in accessible_projects]
    
    if resource_type == 'findings':
        return [item for item in data if hasattr(item, 'project_id') and item.project_id in accessible_project_ids]
    elif resource_type == 'tasks':
        return [item for item in data if hasattr(item, 'project_id') and item.project_id in accessible_project_ids]
    elif resource_type == 'projects':
        return [item for item in data if item.id in accessible_project_ids]
    
    return data

class PermissionManager:
    """Advanced permission management class"""
    
    @staticmethod
    def can_access_project(user_id, user_role, project_id):
        """Check if user can access specific project"""
        return check_resource_access(user_role, 'project', project_id, user_id)
    
    @staticmethod
    def can_edit_finding(user_id, user_role, finding_id):
        """Check if user can edit specific finding"""
        return has_resource_permission(user_role, 'finding', 'edit', finding_id, user_id)
    
    @staticmethod
    def can_assign_task(user_id, user_role, project_id):
        """Check if user can assign tasks in project"""
        return user_role in ['super_admin', 'admin'] or \
               (user_role == 'developer' and check_resource_access(user_role, 'project', project_id, user_id))
    
    @staticmethod
    def get_dashboard_data(user_id, user_role):
        """Get dashboard data based on user permissions"""
        from models import Finding, Task, Project
        
        if user_role in ['super_admin', 'admin']:
            projects = Project.query.all()
            findings = Finding.query.all()
            tasks = Task.query.all()
        else:
            accessible_projects = get_accessible_projects(user_id, user_role)
            project_ids = [p.id for p in accessible_projects]
            
            projects = accessible_projects
            findings = Finding.query.filter(Finding.project_id.in_(project_ids)).all() if project_ids else []
            tasks = Task.query.filter(Task.project_id.in_(project_ids)).all() if project_ids else []
        
        return {
            'projects': projects,
            'findings': findings,
            'tasks': tasks,
            'project_count': len(projects),
            'finding_count': len(findings),
            'task_count': len(tasks)
        }
    
    @staticmethod
    def validate_bulk_operation(user_id, user_role, resource_type, resource_ids, action):
        """Validate bulk operations on multiple resources"""
        for resource_id in resource_ids:
            if not has_resource_permission(user_role, resource_type, action, resource_id, user_id):
                return False, f"Access denied to {resource_type} {resource_id}"
        return True, "All resources accessible"

# API endpoint for permission checking
def check_permissions_api():
    """API endpoint to check user permissions"""
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    user = User.query.get(session['user_id'])
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    permissions = get_user_permissions(user.role)
    accessible_projects = get_accessible_projects(user.id, user.role)
    
    return jsonify({
        'role': user.role,
        'permissions': permissions,
        'accessible_projects': [{'id': p.id, 'name': p.name} for p in accessible_projects]
    })

def audit_permission_check(user_id, resource_type, resource_id, action, granted):
    """Audit permission checks for security monitoring"""
    from models import ActivityLog
    from app import db
    
    audit_log = ActivityLog(
        user_id=user_id,
        action=f"permission_check_{action}_{resource_type}",
        details=json.dumps({
            'resource_id': resource_id,
            'granted': granted,
            'timestamp': str(datetime.utcnow())
        })
    )
    db.session.add(audit_log)
    db.session.commit()