# CHAPTER 4. EXPECTED OUTCOMES

## 4.1. Overview

Based on the objectives and requirements of the project "Building a Data Analysis and Decision Support System for Instructors on Open edX Platform", this chapter presents the expected outcomes of the system. The outcomes are categorized into functional, technical, effectiveness, and documentation aspects.

---

## 4.2. Expected Functional Outcomes

### 4.2.1. Early Warning Functionality (MVP - Mandatory)

#### 4.2.1.1. Risk Analysis and Assessment

The system will analyze learner indicators to identify risks of poor performance or dropout:

- **Access Frequency**: Track login frequency and activity time on the system
- **Quiz and Assignment Scores**: Analyze average scores, improvement or decline trends
- **Assignment Submission Progress**: Assess timely completion or late submissions
- **Interaction Level**: Measure participation in forums, discussions, and other interactive activities
- **Learning Progress**: Analyze completion rates of videos, lessons, and courses

**Expected Outcomes**:
- The system can classify learners into 3 risk levels:
  - **High Risk**: Requires immediate intervention
  - **Medium Risk**: Requires monitoring and support
  - **Low Risk**: Stable condition, continue monitoring
- Classification accuracy: **AUC-ROC ≥ 0.75**, **Recall for "high risk" class ≥ 0.70**
- Detection time: Warnings are generated within **24-48 hours** after detecting signs

#### 4.2.1.2. Warning Display Dashboard

The dashboard will provide a visual interface for instructors to monitor and manage learners:

- **List of Learners Requiring Attention**:
  - Display list sorted by risk level
  - Filters: by risk level, course, department, class
  - Search: by name, student ID, email
  - Sorting: by risk score, progress, last activity date

- **Detailed Learner Information**:
  - Basic information: name, student ID, email, class
  - Current risk score and risk level
  - Activity timeline: video views, quiz attempts, forum posts over time
  - Learning progress chart: progress over time
  - Comparison with class average: radar chart or bar chart
  - Warning history: previous warnings and actions taken

- **Intervention Action Suggestions**:
  - Send personalized reminder emails
  - Send system notifications
  - Recommend appropriate support materials
  - Schedule meetings or consultations
  - Suggest supplementary assignments

**Expected Outcomes**:
- Dashboard loads within **< 2 seconds** for lists ≤ 100 learners
- Responsive interface, supports desktop and tablet
- User-friendly: instructors can understand and use after **< 10 minutes** of familiarization

#### 4.2.1.3. Integration with Open edX

The system will be integrated into the Open edX instructor interface:

- **Integration as a Separate Page**:
  - New menu item in instructor dashboard: "Dropout Prediction" or "Student Analytics"
  - Separate page with URL: `/courses/{course_id}/instructor#view-dropout-prediction`
  - Or integrated as a tab in the existing instructor dashboard

- **Integration as a Plugin** (if possible):
  - Plugin can be installed and activated for each course
  - Configurable through course settings

**Expected Outcomes**:
- System integrates smoothly with Open edX without affecting main system performance
- Instructors can access from instructor dashboard without separate login
- Data is automatically synchronized with Open edX

### 4.2.2. Extended Functionality (Based on Capability and Time)

#### 4.2.2.1. Difficult Content Analysis

The system will analyze and summarize issues learners encounter:

- **Forum Questions Aggregation by Topic**:
  - Classify questions by topics/chapters
  - Identify most frequently asked topics
  - Analyze question sentiment (difficulty, questions, feedback)

- **Problematic Content Detection**:
  - Videos with high skip rates
  - Quizzes with high error rates or excessive completion time
  - Assignments with high late submission rates

**Expected Outcomes**:
- Summary report of difficult content by course
- Suggestions for content improvement: clarification, additional examples, difficulty adjustment

#### 4.2.2.2. Teaching Effectiveness Comparison

The system will provide trend reports across semesters:

- **Comparison Reports**:
  - Compare dropout rates between semesters
  - Compare completion rates and average grades
  - Compare engagement metrics (forum posts, video views)

- **Trends Over Time**:
  - Trend charts of important metrics
  - Analysis of change causes (if any)

**Expected Outcomes**:
- Instructors can evaluate effectiveness of changes in content or teaching methods
- Data supports course improvement decisions

#### 4.2.2.3. Automatic Learner Clustering

The system will use clustering to group learners:

- **Grouping Based on Learning Behavior**:
  - Active learner group
  - Passive learner group
  - Struggling learner group
  - High-risk learner group

- **Clustering Applications**:
  - Send appropriate notifications or materials to each group
  - Suggest different intervention strategies

**Expected Outcomes**:
- Accurate clustering with silhouette score ≥ 0.5
- Instructors can customize number of groups and clustering criteria

#### 4.2.2.4. Overview Dashboard

Homepage dashboard displays important indicators:

- **Overview Indicators**:
  - Total learners in course
  - Number of learners with high/medium/low risk
  - Average completion rate
  - Average grade
  - Number of new warnings today/week

- **Daily Tasks**:
  - List of learners requiring immediate intervention
  - Upcoming assignments needing reminders
  - Unanswered forum questions

**Expected Outcomes**:
- Instructors can grasp overall situation in seconds
- Reduce management time and increase intervention effectiveness

#### 4.2.2.5. Content Engagement Analysis

The system will analyze interaction levels with each learning material:

- **Statistics by Content Type**:
  - Videos: view count, average watch time, completion rate
  - Quizzes: attempt count, average score, completion time
  - Forum: post count, comment count, upvote count
  - Assignments: submission rate, average score

- **Learning Material Quality Assessment**:
  - Identify most interacted content
  - Identify least interacted or problematic content

**Expected Outcomes**:
- Instructors can assess quality and effectiveness of each learning material
- Data supports decisions to improve or adjust content

---

## 4.3. Expected Technical Outcomes

### 4.3.1. System Architecture

#### 4.3.1.1. Backend

- **Framework**: Python with Flask or Django
- **API Design**: RESTful API with JSON responses
- **Database**: MySQL or PostgreSQL (depending on Open edX setup)
- **Data Processing**: pandas, numpy for data processing
- **Machine Learning**: scikit-learn, XGBoost for prediction models

**Expected Outcomes**:
- API response time < 500ms for common endpoints
- System can handle ≥ 50 concurrent requests
- Code organized by modules, easy to maintain and extend

#### 4.3.1.2. Frontend

- **Framework**: React or Vue.js
- **Charts**: Chart.js, Recharts, or D3.js
- **UI Framework**: Material-UI, Ant Design, or AdminLTE template
- **State Management**: Redux or Vuex (if needed)

**Expected Outcomes**:
- Responsive interface, supports desktop and tablet
- Load time < 3 seconds for first page
- Smooth animations and transitions
- Cross-browser compatibility (Chrome, Firefox, Safari, Edge)

#### 4.3.1.3. Database

- **Schema Design**: 
  - Raw data tables: `enrollments`, `h5p_scores`, `video_progress`, `mooc_progress`, `mooc_grades`, `mooc_discussions`
  - Aggregated tables: `raw_data` (aggregated features)
  - Prediction tables: `predictions`, `risk_scores`
  - Metadata tables: `batch_metadata`, `model_versions`

- **Indexes**: Optimized for frequent queries
- **Data Retention**: Data storage and backup policies

**Expected Outcomes**:
- Query performance: complex queries run in < 1 second
- Database can scale to hundreds of thousands of records
- Data backed up regularly

### 4.3.2. Integration with Open edX

#### 4.3.2.1. API Integration

- **Connection to Open edX APIs**:
  - Enrollment API: Get learner list
  - Grades API: Get scores
  - Progress API: Get learning progress
  - Discussion API: Get forum data

- **Authentication**: Use OAuth2 or session-based authentication from Open edX

**Expected Outcomes**:
- Stable connection to Open edX APIs
- Handle cases when APIs are unavailable (retry, fallback)
- Data automatically synchronized on schedule (daily or real-time)

#### 4.3.2.2. Database Integration (If Possible)

- **Direct Database Access**: Direct queries to Open edX database (if permitted)
- **Data Sync**: Synchronize data between Open edX and analysis system

**Expected Outcomes**:
- Data synchronized accurately and timely
- No impact on Open edX database performance

### 4.3.3. Machine Learning Model

#### 4.3.3.1. Model Performance

- **Metrics**:
  - AUC-ROC ≥ 0.75
  - Precision ≥ 0.70 for "high risk" class
  - Recall ≥ 0.70 for "high risk" class
  - F1-score ≥ 0.70

- **Model Type**: XGBoost or Gradient Boosting (may try ensemble)

**Expected Outcomes**:
- Model can accurately predict dropout risk
- Model retrained periodically with new data
- Feature importance analyzed and explainable

#### 4.3.3.2. Feature Engineering

- **Features Used**:
  - Enrollment features: weeks_since_enrollment, enrollment_mode
  - Progress features: completion_rate, progress_percent, days_since_last_activity
  - Activity features: activity_consistency, max_inactive_gap_days
  - Performance features: relative_completion, is_struggling
  - Interaction features: discussion_engagement_rate, interaction_score

**Expected Outcomes**:
- Features selected and optimized
- No data leakage (no future information used)
- Features meaningful and explainable

---

## 4.4. Expected Effectiveness Outcomes

### 4.4.1. Effectiveness for Instructors

- **Time Savings**:
  - Reduce learner monitoring time from **several hours/week to < 30 minutes/week**
  - Automate detection of learners with issues

- **Increased Intervention Effectiveness**:
  - Intervene earlier, before learners completely drop out
  - Action suggestions help instructors know what to do

- **Improved Teaching Quality**:
  - Data supports decisions to improve course content
  - Detect problematic content sections

### 4.4.2. Effectiveness for Learners

- **Reduced Dropout Rate**:
  - Goal: Reduce dropout rate **≥ 10%** compared to before system implementation
  - Early intervention helps learners receive timely support

- **Improved Learning Experience**:
  - Learners receive support appropriate to their situation
  - Course content improved based on feedback

### 4.4.3. Effectiveness for Organization

- **Resource Optimization**:
  - Focus support on learners who truly need it
  - Reduce costs due to learner dropout

- **Improved Education Quality**:
  - Data supports decisions to improve training programs
  - Increase course completion rates

---

## 4.5. Expected Documentation Outcomes

### 4.5.1. User Manual

- **User Manual for Instructors**:
  - Login and dashboard access guide
  - Guide to reading and understanding warnings
  - Guide to using filters and search
  - Guide to performing intervention actions
  - FAQ and troubleshooting

**Expected Outcomes**:
- Easy-to-understand documentation with illustrations
- Instructors can use system after reading documentation

### 4.5.2. Technical Documentation

- **Technical Documentation**:
  - System architecture
  - Database schema and ER diagram
  - API documentation
  - Code structure and coding conventions
  - Deployment guide

**Expected Outcomes**:
- Other developers can understand and maintain code
- Easy to deploy and scale system

### 4.5.3. Evaluation Report

- **Real-world Test Report**:
  - Testing with 1-2 real courses
  - Model performance evaluation results
  - Feedback from instructors using the system
  - System effectiveness analysis

**Expected Outcomes**:
- Detailed report with specific data
- Objective evaluation of system effectiveness and limitations

### 4.5.4. Source Code

- **Code Repository**:
  - Code well-organized with comments
  - README with setup and run instructions
  - Version control with Git
  - License and contribution guidelines

**Expected Outcomes**:
- Good code quality, readable and maintainable
- Can be deployed and run on new environments

---

## 4.6. Evaluation Criteria and Expected Outcomes

Based on the project evaluation criteria, expected outcomes are summarized as follows:

### 4.6.1. Early Warning Functionality (40%)

**Expected Outcomes**:
- ✅ System accurately analyzes learning indicators
- ✅ Classifies learners into 3 risk levels with high accuracy (AUC ≥ 0.75)
- ✅ Warnings generated timely (24-48 hours)
- ✅ Dashboard displays complete information and action suggestions
- ✅ Successfully integrated with Open edX

### 4.6.2. Dashboard Interface (20%)

**Expected Outcomes**:
- ✅ User-friendly, easy-to-use interface
- ✅ Responsive design, supports multiple devices
- ✅ Fast load time (< 2-3 seconds)
- ✅ Clear and understandable visualizations

### 4.6.3. Scalability and Integration (15%)

**Expected Outcomes**:
- ✅ Smooth integration with Open edX
- ✅ Well-organized code, easy to extend
- ✅ Database can scale
- ✅ Flexible API design, easy to integrate with other systems

### 4.6.4. Additional Functionality (15%)

**Expected Outcomes** (based on capability and time):
- ✅ Difficult content analysis
- ✅ Teaching effectiveness comparison
- ✅ Automatic learner clustering
- ✅ Overview dashboard
- ✅ Content engagement analysis

### 4.6.5. Documentation and Report (10%)

**Expected Outcomes**:
- ✅ Complete and easy-to-understand user manual
- ✅ Detailed technical documentation
- ✅ Evaluation report with specific data
- ✅ Well-organized source code

---

## 4.7. Conclusion

The expected outcomes of the system are detailed in this chapter, including:

1. **Functionality**: Early warning system operates accurately and timely, along with extended functionality based on capability
2. **Technical**: Robust system architecture, good integration with Open edX, effective ML model
3. **Effectiveness**: Reduced dropout rate, time savings for instructors, improved education quality
4. **Documentation**: Complete and quality documentation, supporting both users and developers

With these expected outcomes, the system will meet the project requirements and bring practical value to instructors and learners on the Open edX platform.
