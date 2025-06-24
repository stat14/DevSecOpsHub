# Nexus Platform

## Overview

Nexus Platform is a comprehensive business management application built with Flask that provides three integrated modules:

1. **Nexus Secure** - Penetration testing management with findings tracking and reporting
2. **Nexus Flow** - Agile project management with Kanban boards for development teams  
3. **Admin Panel** - Centralized user and project management

The platform supports role-based access control with different user types (super_admin, admin, pentester, developer, client) and provides specialized dashboards for each role.

## System Architecture

**Backend Framework**: Flask with SQLAlchemy ORM
**Database**: SQLite (development) with PostgreSQL support configured
**Frontend**: Server-side rendered templates using Jinja2 with Bootstrap 5
**Authentication**: Session-based authentication with JWT support configured
**Deployment**: Gunicorn WSGI server with autoscale deployment target

The application follows a modular blueprint architecture with separate modules for each major feature area.

## Key Components

### Authentication System (`auth.py`)
- Session-based user authentication
- Role-based access control decorators
- Activity logging for security events
- Password hashing with Werkzeug

### Database Models (`models.py`)
- **User**: Manages user accounts with role-based permissions
- **Project**: Handles both pentest and development projects
- **Finding**: Security vulnerabilities for pentest projects
- **Task**: Development tasks with status tracking
- **ActivityLog**: Audit trail for user actions
- **UserProject**: Many-to-many relationship for project assignments

### Business Logic Modules
- **Admin Panel** (`admin.py`): User management, project oversight, system statistics
- **Secure Module** (`secure.py`): Penetration testing workflow and findings management
- **Flow Module** (`flow.py`): Agile development with Kanban boards
- **Client Portal** (`client.py`): Read-only access for clients to view project status
- **Reports** (`reports.py`): PDF report generation using ReportLab

### Frontend Architecture
- Bootstrap 5 responsive design
- Modular template system with reusable components
- JavaScript modules for interactive features (Kanban boards, findings management)
- Role-specific dashboards and navigation

## Data Flow

1. **Authentication Flow**: Users log in → Session established → Role-based dashboard redirect
2. **Project Management**: Admin creates projects → Assigns users → Users access via role-specific modules
3. **Pentest Workflow**: Pentesters create findings → Generate reports → Clients view results
4. **Development Workflow**: Tasks managed via Kanban boards → Status updates → Progress tracking
5. **Activity Logging**: All user actions logged for audit purposes

## External Dependencies

### Python Packages
- **Flask**: Web framework and routing
- **Flask-SQLAlchemy**: Database ORM
- **Flask-JWT-Extended**: JWT token management
- **Flask-Login**: User session management
- **ReportLab**: PDF report generation
- **Werkzeug**: Password hashing and WSGI utilities
- **Gunicorn**: Production WSGI server
- **psycopg2-binary**: PostgreSQL database adapter

### Frontend Dependencies
- **Bootstrap 5**: UI framework and responsive design
- **Font Awesome**: Icon library
- **TinyMCE**: Rich text editor for findings descriptions
- **Chart.js**: Data visualization for dashboards

## Deployment Strategy

The application is configured for deployment on Replit with:
- **Development**: Built-in Flask development server with debug mode
- **Production**: Gunicorn WSGI server with automatic scaling
- **Database**: SQLite for development, PostgreSQL packages included for production
- **Static Assets**: Served via CDN for performance
- **Security**: Environment variables for secrets and database URLs

The `.replit` configuration supports both development workflows and production deployment with appropriate server binding and port configuration.

## Changelog
- June 24, 2025. Initial setup

## User Preferences

Preferred communication style: Simple, everyday language.