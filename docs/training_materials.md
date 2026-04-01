# Green Engine Training Materials

## Table of Contents

1. [Training Overview](#training-overview)
2. [Administrator Training](#administrator-training)
3. [Operator Training](#operator-training)
4. [Viewer Training](#viewer-training)
5. [Hands-on Exercises](#hands-on-exercises)
6. [Assessment Quizzes](#assessment-quizzes)
7. [Certification Program](#certification-program)
8. [Training Resources](#training-resources)

## Training Overview

### Training Objectives

By the end of this training program, participants will be able to:
- Navigate the Green Engine dashboard effectively
- Understand their role-specific responsibilities
- Use system features appropriate to their access level
- Troubleshoot common issues
- Follow security best practices
- Contribute to system optimization

### Training Structure

- **Self-paced online modules** (2-4 hours per role)
- **Hands-on exercises** with live system
- **Assessment quizzes** to verify understanding
- **Certification** upon successful completion
- **Ongoing support** and refresher training

### Prerequisites

- Basic computer literacy
- Web browser familiarity
- Understanding of greenhouse operations (for operators)
- Basic networking knowledge (for administrators)

## Administrator Training

### Module 1: System Overview and Architecture

#### Learning Objectives
- Understand Green Engine system architecture
- Know the role of each component
- Understand data flow and system integration

#### Key Topics
1. **System Components**
   - API server (FastAPI)
   - Dashboard (Streamlit)
   - Database (PostgreSQL)
   - MQTT broker (Mosquitto)
   - Machine Learning services

2. **Data Flow**
   - Device → MQTT → API → Database
   - Database → API → Dashboard
   - ML Pipeline → Predictions → Dashboard

3. **Security Architecture**
   - JWT authentication
   - Role-based access control
   - TLS encryption
   - Audit logging

#### Hands-on Exercise
- Access system architecture diagram
- Trace data flow from device to dashboard
- Identify security layers

### Module 2: User Management and Security

#### Learning Objectives
- Create and manage user accounts
- Configure roles and permissions
- Implement security best practices

#### Key Topics
1. **User Management**
   - Creating new users
   - Assigning roles (Admin, Operator, Viewer)
   - Managing user permissions
   - Account lifecycle management

2. **Security Configuration**
   - Password policies
   - Session management
   - API key management
   - Audit log review

3. **Access Control**
   - Role-based permissions
   - Resource-level access
   - Time-based access controls

#### Hands-on Exercise
- Create a new operator user
- Configure role permissions
- Review audit logs
- Test access controls

### Module 3: System Configuration and Monitoring

#### Learning Objectives
- Configure system parameters
- Set up monitoring and alerts
- Manage system performance

#### Key Topics
1. **System Configuration**
   - Sensor thresholds
   - Alert rules
   - Data retention policies
   - Backup schedules

2. **Monitoring Setup**
   - Prometheus metrics
   - Grafana dashboards
   - Log aggregation
   - Performance monitoring

3. **Maintenance Procedures**
   - Database maintenance
   - System updates
   - Backup and recovery
   - Performance optimization

#### Hands-on Exercise
- Configure sensor thresholds
- Set up alert rules
- Review monitoring dashboards
- Perform system maintenance tasks

### Module 4: Device Management and Integration

#### Learning Objectives
- Onboard new devices
- Manage device configurations
- Troubleshoot device issues

#### Key Topics
1. **Device Onboarding**
   - Device registration
   - Certificate management
   - Network configuration
   - Testing and validation

2. **Device Management**
   - Firmware updates
   - Configuration changes
   - Performance monitoring
   - Troubleshooting

3. **Integration Management**
   - MQTT configuration
   - Data format standards
   - Command protocols
   - Error handling

#### Hands-on Exercise
- Onboard a new sensor device
- Configure device parameters
- Test data transmission
- Troubleshoot connection issues

## Operator Training

### Module 1: Dashboard Navigation and Overview

#### Learning Objectives
- Navigate the dashboard effectively
- Understand data visualization
- Access relevant information quickly

#### Key Topics
1. **Dashboard Layout**
   - Main navigation tabs
   - Data visualization components
   - Time range selection
   - Export capabilities

2. **Real-time Monitoring**
   - Sensor data display
   - Alert notifications
   - System status indicators
   - Performance metrics

3. **Data Interpretation**
   - Understanding sensor readings
   - Identifying trends and patterns
   - Recognizing anomalies
   - Making data-driven decisions

#### Hands-on Exercise
- Navigate through all dashboard tabs
- Interpret sensor data charts
- Identify system status indicators
- Export data for analysis

### Module 2: Tray and Crop Management

#### Learning Objectives
- Manage tray information effectively
- Track crop progress
- Record growth measurements

#### Key Topics
1. **Tray Management**
   - Creating new trays
   - Updating tray information
   - Tracking crop progress
   - Managing batch information

2. **Growth Monitoring**
   - Recording measurements
   - Tracking growth rates
   - Identifying growth issues
   - Optimizing growing conditions

3. **Harvest Planning**
   - Yield predictions
   - Harvest timing
   - Quality assessment
   - Production planning

#### Hands-on Exercise
- Create a new tray record
- Update tray information
- Record growth measurements
- Review yield predictions

### Module 3: Alert Management and Response

#### Learning Objectives
- Understand alert types and levels
- Respond to alerts appropriately
- Document actions taken

#### Key Topics
1. **Alert System**
   - Types of alerts (system, environmental, crop)
   - Alert levels (info, warning, critical)
   - Alert lifecycle (active, acknowledged, resolved)

2. **Alert Response**
   - Acknowledging alerts
   - Taking corrective actions
   - Resolving alerts
   - Documenting responses

3. **Preventive Actions**
   - Monitoring trends
   - Proactive interventions
   - System optimization
   - Best practices

#### Hands-on Exercise
- Review active alerts
- Acknowledge and resolve alerts
- Document actions taken
- Implement preventive measures

### Module 4: Device Commands and Automation

#### Learning Objectives
- Send commands to devices
- Monitor command execution
- Troubleshoot command issues

#### Key Topics
1. **Device Commands**
   - Types of commands (irrigation, lighting, ventilation)
   - Command parameters
   - Command execution
   - Status monitoring

2. **Automation Management**
   - Automated responses
   - Rule-based actions
   - Scheduling commands
   - Override capabilities

3. **Command History**
   - Viewing command logs
   - Requeuing failed commands
   - Performance analysis
   - Optimization opportunities

#### Hands-on Exercise
- Send irrigation command
- Monitor command execution
- Review command history
- Requeue failed commands

## Viewer Training

### Module 1: Dashboard Access and Navigation

#### Learning Objectives
- Access the dashboard
- Navigate read-only features
- Understand data display

#### Key Topics
1. **Dashboard Access**
   - Login process
   - Navigation overview
   - Read-only features
   - Data visualization

2. **Information Access**
   - Sensor data viewing
   - Tray information
   - Alert monitoring
   - Analytics and reports

3. **Data Export**
   - Exporting sensor data
   - Generating reports
   - Data analysis tools
   - Sharing information

#### Hands-on Exercise
- Login to dashboard
- Navigate through all tabs
- View sensor data and analytics
- Export data for analysis

### Module 2: Data Interpretation and Analysis

#### Learning Objectives
- Interpret sensor data effectively
- Understand analytics and trends
- Make informed observations

#### Key Topics
1. **Sensor Data Interpretation**
   - Temperature, humidity, light readings
   - Soil moisture and EC values
   - CO2 levels and air quality
   - Optimal ranges and thresholds

2. **Analytics Understanding**
   - Growth rate calculations
   - Yield predictions
   - Performance metrics
   - Trend analysis

3. **Report Generation**
   - Custom time ranges
   - Data filtering
   - Report formatting
   - Data visualization

#### Hands-on Exercise
- Analyze sensor data trends
- Interpret growth analytics
- Generate custom reports
- Identify performance patterns

## Hands-on Exercises

### Exercise 1: System Setup and Configuration

**Objective**: Set up a new Green Engine system from scratch

**Tasks**:
1. Install and configure PostgreSQL database
2. Set up MQTT broker
3. Configure API server
4. Launch dashboard
5. Create initial user accounts
6. Configure sensor thresholds

**Expected Outcome**: Fully functional system ready for device integration

### Exercise 2: Device Integration

**Objective**: Integrate a new sensor device into the system

**Tasks**:
1. Register device in system
2. Generate device certificates
3. Configure device network settings
4. Test MQTT connection
5. Validate data transmission
6. Verify dashboard display

**Expected Outcome**: Device successfully sending data to dashboard

### Exercise 3: Alert System Testing

**Objective**: Test and validate the alert system

**Tasks**:
1. Configure alert thresholds
2. Simulate threshold violations
3. Verify alert generation
4. Test alert acknowledgment
5. Resolve alerts
6. Review alert history

**Expected Outcome**: Alert system functioning correctly

### Exercise 4: Machine Learning Integration

**Objective**: Set up and test ML prediction capabilities

**Tasks**:
1. Prepare training data
2. Train ML models
3. Deploy prediction service
4. Test prediction endpoints
5. Verify dashboard integration
6. Monitor model performance

**Expected Outcome**: ML predictions available in dashboard

### Exercise 5: User Management and Security

**Objective**: Implement comprehensive user management

**Tasks**:
1. Create user roles and permissions
2. Add new users with different roles
3. Test access controls
4. Review audit logs
5. Implement security policies
6. Test authentication flows

**Expected Outcome**: Secure user management system

## Assessment Quizzes

### Administrator Assessment

**Question 1**: What are the main components of the Green Engine system architecture?
- [ ] API server, Dashboard, Database, MQTT broker
- [ ] Web server, Database, Email service
- [ ] Mobile app, Cloud storage, Analytics
- [ ] All of the above

**Question 2**: How do you create a new user with operator permissions?
- [ ] Use the User Management interface in Admin tab
- [ ] Edit the database directly
- [ ] Send an email to the system
- [ ] Use command line tools only

**Question 3**: What is the purpose of JWT tokens in the authentication system?
- [ ] To store user passwords
- [ ] To provide secure, stateless authentication
- [ ] To encrypt database connections
- [ ] To compress data transmission

### Operator Assessment

**Question 1**: What should you do when you receive a critical temperature alert?
- [ ] Ignore it and continue with other tasks
- [ ] Acknowledge the alert and investigate
- [ ] Wait for someone else to handle it
- [ ] Delete the alert from the system

**Question 2**: How do you send an irrigation command to a device?
- [ ] Call the device manufacturer
- [ ] Use the Device Commands section in Admin tab
- [ ] Send an email to the system
- [ ] Restart the device

**Question 3**: What information is required when creating a new tray?
- [ ] Only the tray code
- [ ] Tray code, device ID, crop type, planted date
- [ ] Just the crop type
- [ ] Only the device ID

### Viewer Assessment

**Question 1**: What can you do with sensor data in the dashboard?
- [ ] View, analyze, and export data
- [ ] Modify sensor readings
- [ ] Delete historical data
- [ ] Change sensor configurations

**Question 2**: How do you export data for external analysis?
- [ ] Take a screenshot
- [ ] Use the Export button in the Analytics tab
- [ ] Copy and paste data
- [ ] Send an email request

**Question 3**: What does the growth rate metric represent?
- [ ] The speed of plant growth over time
- [ ] The number of plants in a tray
- [ ] The temperature of the growing environment
- [ ] The amount of water used

## Certification Program

### Certification Levels

#### Level 1: Basic User (Viewer)
- Complete viewer training modules
- Pass viewer assessment quiz (80% or higher)
- Demonstrate basic dashboard navigation
- Understand data interpretation

#### Level 2: Operator
- Complete operator training modules
- Pass operator assessment quiz (85% or higher)
- Successfully complete hands-on exercises
- Demonstrate operational competence

#### Level 3: Administrator
- Complete administrator training modules
- Pass administrator assessment quiz (90% or higher)
- Complete all hands-on exercises
- Demonstrate system administration skills

### Certification Process

1. **Complete Training Modules**
   - Self-paced online training
   - Hands-on exercises
   - Peer review and feedback

2. **Pass Assessment**
   - Role-specific quiz
   - Practical demonstration
   - Scenario-based testing

3. **Receive Certification**
   - Digital certificate
   - Badge for email signature
   - Access to advanced features
   - Continuing education opportunities

### Continuing Education

- **Quarterly Updates**: New features and improvements
- **Advanced Training**: Specialized topics and techniques
- **Best Practices**: Industry updates and recommendations
- **Community Forums**: Peer support and knowledge sharing

## Training Resources

### Documentation
- **User Manual**: Comprehensive user guide
- **API Documentation**: Technical reference
- **Troubleshooting Guide**: Problem-solving resources
- **Device Onboarding Guide**: Hardware integration

### Video Tutorials
- **Dashboard Navigation**: Step-by-step walkthrough
- **User Management**: Administrative procedures
- **Device Integration**: Hardware setup and configuration
- **Troubleshooting**: Common issues and solutions

### Interactive Demos
- **Live System Access**: Hands-on practice environment
- **Simulated Scenarios**: Real-world problem solving
- **Virtual Labs**: Safe testing environment
- **Peer Collaboration**: Team-based learning

### Support Resources
- **Help Desk**: Technical support and assistance
- **Knowledge Base**: Searchable documentation
- **Community Forum**: User discussions and tips
- **Expert Consultation**: One-on-one guidance

### Training Schedule

#### Self-Paced Training
- **Available**: 24/7 online access
- **Duration**: 2-4 hours per role
- **Format**: Interactive modules with assessments

#### Instructor-Led Training
- **Schedule**: Monthly sessions
- **Duration**: 4-8 hours per role
- **Format**: Live online or in-person

#### Hands-on Workshops
- **Schedule**: Quarterly sessions
- **Duration**: Full day (8 hours)
- **Format**: Practical exercises with expert guidance

### Training Metrics

#### Completion Tracking
- Module completion rates
- Assessment scores
- Time to completion
- User satisfaction ratings

#### Performance Metrics
- System usage efficiency
- Error reduction rates
- User productivity improvements
- Support ticket reduction

#### Continuous Improvement
- Training feedback analysis
- Content updates and revisions
- New training development
- Best practice integration

---

*For questions about training or to schedule a training session, contact the training team at training@greenengine.com.*
