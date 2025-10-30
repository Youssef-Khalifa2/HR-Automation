# HR Co-Pilot Refined Wireframes & Implementation Guide

## Overview
Based on the original HR platform wireframes, this document outlines the refined implementation plan for Phase 1 of the HR Co-Pilot MVP, including detailed screen specifications, user workflows, and technical implementation details.

## Screen 1: Login Page (`/`)

### Purpose
HR personnel authentication to access the offboarding dashboard.

### Layout & Components
- **Header**: HR Co-Pilot branding with professional logo/icon
- **Main Form**: Centered login card with:
  - Email field with envelope icon
  - Password field with lock icon
  - Login button with primary styling
- **Error Display**: Inline error messages for authentication failures
- **Footer**: Information note about HR-only access

### Technical Implementation
- Template: `templates/index.html`
- Authentication: JWT tokens via `/api/auth/login`
- Validation: Email format and required fields
- Redirection: Successful login → `/dashboard`

### User Experience
- Clean, professional design matching corporate standards
- Clear feedback for login errors
- Remember token in localStorage for session persistence
- Auto-redirect if already authenticated

---

## Screen 2: Dashboard (`/dashboard`)

### Purpose
Central hub for HR users to monitor resignation workflow status and access key functions.

### Layout & Components

#### Header Section
- Page title: "Dashboard"
- User welcome message (optional)

#### Statistics Cards (4 columns)
1. **Total Submissions**: Count of all resignation records
2. **Pending Approvals**: Submissions awaiting leader/CHM action
3. **Completed This Month**: Successfully processed offboardings
4. **Exit Interviews**: Scheduled or pending interviews

#### Recent Submissions Table
- Columns: Employee, Department, Status, Submitted Date, Actions
- Sorting: By submission date (newest first)
- Pagination: 10 items per view
- Actions: View details button

#### Quick Actions Panel
- New Submission button
- Refresh Data button
- View Reports button (future feature)

#### Pending Items List
- Shows up to 5 items needing attention
- Groups by type: Leader approval, CHM approval, Schedule interview
- Direct links to relevant submissions

### Technical Implementation
- Template: `templates/dashboard.html`
- Data Source: `/api/submissions` with filtering
- Real-time Updates: Manual refresh button
- Responsive Design: Bootstrap grid system

### User Experience
- At-a-glance view of current workload
- Quick access to most recent submissions
- Clear visual indicators of pending items
- Mobile-friendly responsive layout

---

## Screen 3: Submissions Management (`/submissions`)

### Purpose
Comprehensive interface for managing all resignation submissions with filtering, CRUD operations, and detailed views.

### Layout & Components

#### Filter Section
- **Status Filter**: Dropdown for resignation status
- **Department Filter**: Text input for department search
- **Date Range**: From/To date pickers
- **Apply Button**: Execute filter with validation

#### Actions Bar
- New Submission button (opens modal)
- Export button (future feature)
- Results count display

#### Submissions Table
- **Columns**:
  - Employee (Name + Email)
  - Department (badge style)
  - Position
  - Status (color-coded badge)
  - Exit Interview Status
  - Last Working Day
  - Created Date
  - Actions (View, Edit, Delete)

#### Pagination
- Bottom navigation with page numbers
- Items per page configuration

#### Create/Edit Modal
- **Employee Information**: Name, Email, Employee ID
- **Employment Details**: Department, Position, Hire Date
- **Resignation Details**: Resignation Date, Last Working Day, Notice Period
- **Options**: Probation period checkbox
- **Validation**: Required fields, email format, date logic

#### View Details Modal
- **Employee Info**: Complete employee details
- **Employment Details**: All job-related information
- **Workflow Status**: Current status and approval stages
- **Additional Information**: Medical card, vendor mail status
- **Notes Section**: Leader, CHM, and interview notes

### Technical Implementation
- Template: `templates/submissions.html`
- API Endpoints: `/api/submissions` (GET, POST, PATCH, DELETE)
- JavaScript: Dynamic filtering, modal management, form validation
- Data Validation: Pydantic schemas with comprehensive rules

### User Experience
- Powerful filtering for finding specific submissions
- Inline editing for quick updates
- Detailed view for complete information
- Confirmation dialogs for destructive actions
- Loading states and error handling

---

## Screen 4: User Management (`/users`)

### Purpose *(Future Enhancement)*
Manage user accounts with role-based access control.

### Planned Components
- User list with roles and status
- Create new users (HR only)
- Edit user details and roles
- Deactivate/activate users
- Role assignment (HR, Leader, CHM, IT)

---

## Authentication & Security

### JWT Token Management
- **Token Storage**: Local storage for persistence
- **Auto-refresh**: Token expiration handling
- **Logout**: Clear local storage and redirect

### Role-Based Access Control
- **HR Users**: Full access to dashboard and CRUD operations
- **Other Roles**: Email-based signed links only (Phase 2+)
- **API Protection**: All endpoints require valid JWT token
- **Route Protection**: Client-side route guards

### Security Features
- Password hashing with bcrypt
- CORS configuration for production domains
- Input sanitization and validation
- SQL injection prevention via SQLAlchemy

---

## Technical Architecture

### Frontend Stack
- **Framework**: Vanilla JavaScript with ES6+ features
- **UI Framework**: Bootstrap 5 with custom theming
- **HTTP Client**: Axios for API communication
- **Icons**: Font Awesome 6
- **Templating**: Jinja2 templates

### Backend Stack
- **API Framework**: FastAPI with Python 3.8+
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Authentication**: JWT tokens with bcrypt password hashing
- **Validation**: Pydantic schemas for request/response

### Database Schema
- **Users**: Role-based authentication and authorization
- **Submissions**: Core resignation workflow data
- **Assets**: IT asset tracking and clearance

### API Design
- **RESTful**: Standard HTTP methods and status codes
- **Versioning**: `/api/v1/` prefix for future compatibility
- **Documentation**: Auto-generated OpenAPI/Swagger specs
- **Error Handling**: Consistent error response format

---

## Responsive Design

### Breakpoints
- **Desktop**: 1024px+ (full sidebar navigation)
- **Tablet**: 768px-1023px (collapsed sidebar)
- **Mobile**: <768px (stacked layout)

### Mobile Considerations
- Collapsible navigation menu
- Touch-friendly button sizes
- Simplified table views
- Optimized modal layouts

---

## Future Enhancements (Phase 2+)

### Email Integration
- Automated approval emails
- Signed links for external approvers
- Reminder system for pending items
- Email template management

### Advanced Features
- File attachment support
- Approval workflow customization
- Reporting and analytics
- Integration with HR systems

### Performance Optimizations
- Data caching strategies
- Lazy loading for large datasets
- Background job processing
- API rate limiting

---

## Testing Strategy

### Unit Tests
- Model validation and relationships
- CRUD operations
- Authentication logic
- Business rules

### Integration Tests
- API endpoint functionality
- Database operations
- Authentication flows
- Error handling

### End-to-End Tests
- Complete user workflows
- Form submissions
- Navigation flows
- Cross-browser compatibility

---

## Deployment Considerations

### Environment Configuration
- Environment-specific settings
- Secret management
- Database connection pooling
- CORS configuration

### Performance Monitoring
- Application logging
- Performance metrics
- Error tracking
- User analytics

### Security Hardening
- HTTPS enforcement
- Security headers
- Input validation
- Dependency scanning

This refined wireframe document serves as the implementation guide for Phase 1, ensuring all components are built according to specifications and provide a solid foundation for future enhancements.