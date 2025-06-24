"""
Real-time notifications system using WebSocket and Redis
"""
from flask import session, current_app
from flask_socketio import emit, join_room, leave_room
from flask_mail import Message
from app import socketio, mail, redis_client
import json
from datetime import datetime
import threading

def send_notification(user_id, title, message, notification_type='info', project_id=None):
    """Send real-time notification to user"""
    notification_data = {
        'id': f"{datetime.now().timestamp()}",
        'title': title,
        'message': message,
        'type': notification_type,
        'timestamp': datetime.now().isoformat(),
        'project_id': project_id,
        'read': False
    }
    
    # Store in Redis for persistence
    if redis_client:
        redis_client.lpush(f"notifications:{user_id}", json.dumps(notification_data))
        redis_client.ltrim(f"notifications:{user_id}", 0, 99)  # Keep last 100 notifications
    
    # Send real-time notification
    socketio.emit('notification', notification_data, room=f"user_{user_id}")
    
    return notification_data

def send_email_notification(to_email, subject, template_name, **kwargs):
    """Send email notification asynchronously"""
    def send_async_email(app, msg):
        with app.app_context():
            try:
                mail.send(msg)
            except Exception as e:
                current_app.logger.error(f"Failed to send email: {e}")
    
    msg = Message(
        subject=subject,
        recipients=[to_email],
        html=render_email_template(template_name, **kwargs)
    )
    
    thread = threading.Thread(
        target=send_async_email, 
        args=(current_app._get_current_object(), msg)
    )
    thread.start()

def render_email_template(template_name, **kwargs):
    """Render email template"""
    templates = {
        'project_assignment': f"""
        <h2>Project Assignment Notification</h2>
        <p>Dear {kwargs.get('user_name', 'User')},</p>
        <p>You have been assigned to project: <strong>{kwargs.get('project_name', 'Unknown')}</strong></p>
        <p>Project Description: {kwargs.get('project_description', 'No description available')}</p>
        <p>Please log in to your dashboard to view project details.</p>
        <br>
        <p>Best regards,<br>Nexus Platform Team</p>
        """,
        'finding_created': f"""
        <h2>New Security Finding</h2>
        <p>A new {kwargs.get('severity', 'unknown')} severity finding has been reported:</p>
        <p><strong>Title:</strong> {kwargs.get('finding_title', 'Unknown')}</p>
        <p><strong>Project:</strong> {kwargs.get('project_name', 'Unknown')}</p>
        <p>Please review the finding in your dashboard.</p>
        <br>
        <p>Best regards,<br>Nexus Platform Team</p>
        """,
        'task_assignment': f"""
        <h2>Task Assignment</h2>
        <p>You have been assigned a new task:</p>
        <p><strong>Task:</strong> {kwargs.get('task_title', 'Unknown')}</p>
        <p><strong>Project:</strong> {kwargs.get('project_name', 'Unknown')}</p>
        <p><strong>Priority:</strong> {kwargs.get('priority', 'Normal')}</p>
        <p>Please check your dashboard for more details.</p>
        <br>
        <p>Best regards,<br>Nexus Platform Team</p>
        """
    }
    
    return templates.get(template_name, f"<p>{kwargs.get('message', 'Notification')}</p>")

def get_user_notifications(user_id, limit=50):
    """Get user notifications from Redis"""
    if not redis_client:
        return []
    
    notifications = redis_client.lrange(f"notifications:{user_id}", 0, limit-1)
    return [json.loads(notif) for notif in notifications]

def mark_notification_read(user_id, notification_id):
    """Mark a notification as read"""
    if not redis_client:
        return False
    
    notifications = redis_client.lrange(f"notifications:{user_id}", 0, -1)
    for i, notif_json in enumerate(notifications):
        notif = json.loads(notif_json)
        if notif['id'] == notification_id:
            notif['read'] = True
            redis_client.lset(f"notifications:{user_id}", i, json.dumps(notif))
            return True
    return False

@socketio.on('connect')
def handle_connect():
    """Handle WebSocket connection"""
    if 'user_id' in session:
        join_room(f"user_{session['user_id']}")
        emit('connected', {'status': 'Connected to notifications'})

@socketio.on('disconnect')
def handle_disconnect():
    """Handle WebSocket disconnection"""
    if 'user_id' in session:
        leave_room(f"user_{session['user_id']}")

@socketio.on('mark_read')
def handle_mark_read(data):
    """Handle marking notification as read"""
    if 'user_id' in session:
        notification_id = data.get('notification_id')
        if mark_notification_read(session['user_id'], notification_id):
            emit('notification_read', {'notification_id': notification_id})