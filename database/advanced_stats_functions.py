# Add these functions to MOOCH5PDataFetcher class before aggregate_raw_data method
# Insert around line 927 (before aggregate_raw_data)

    # ==================== ADVANCED STATS APIs ====================
    
    def fetch_activity_stats_summary(self, course_id: str) -> Optional[Dict]:
        """
        Fetch Activity Statistics từ Advanced Stats API
        Note: API trả về course-level summary, không phải per-user
        """
        try:
            encoded_course_id = self.url_encode_course_id(course_id)
            url = f"{self.mooc_base_url}/stats/activity/{encoded_course_id}/"
            
            params = {
                'days': 90,  # 90 ngày gần nhất
                'group_by': 'day'
            }
            
            response = self.session.get(url, params=params, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    logger.info(f"Activity stats fetched: {data.get('summary', {}).get('total_activities', 0)} total activities")
                    return data
            else:
                logger.warning(f"Activity stats API returned {response.status_code}")
                
        except Exception as e:
            logger.error(f"Error fetching activity stats: {e}")
        
        return None
    
    def fetch_assessment_stats_summary(self, course_id: str) -> Optional[Dict]:
        """
        Fetch Assessment Statistics từ Advanced Stats API
        Note: API trả về course-level summary
        """
        try:
            encoded_course_id = self.url_encode_course_id(course_id)
            url = f"{self.mooc_base_url}/stats/assessment/{encoded_course_id}/"
            
            params = {
                'days': 90
            }
            
            response = self.session.get(url, params=params, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    logger.info(f"Assessment stats fetched: {data.get('summary', {}).get('total_attempts', 0)} total attempts")
                    return data
            else:
                logger.warning(f"Assessment stats API returned {response.status_code}")
                
        except Exception as e:
            logger.error(f"Error fetching assessment stats: {e}")
        
        return None
    
    def fetch_progress_stats_summary(self, course_id: str) -> Optional[Dict]:
        """
        Fetch Progress Statistics từ Advanced Stats API  
        Note: API trả về course-level summary
        """
        try:
            encoded_course_id = self.url_encode_course_id(course_id)
            url = f"{self.mooc_base_url}/stats/progress/{encoded_course_id}/"
            
            params = {
                'days': 90
            }
            
            response = self.session.get(url, params=params, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    logger.info(f"Progress stats fetched: {data.get('summary', {}).get('total_students', 0)} total students")
                    return data
            else:
                logger.warning(f"Progress stats API returned {response.status_code}")
                
        except Exception as e:
            logger.error(f"Error fetching progress stats: {e}")
        
        return None
    
    def calculate_derived_activity_features(
        self, 
        user_id: int, 
        course_id: str,
        mooc_progress: Optional[Dict] = None
    ) -> Dict:
        """
        Calculate activity-based features từ existing data
        
        Vì Advanced Stats API chỉ trả về course-level summary,
        ta sẽ calculate features từ existing user data
        """
        features = {
            'problem_attempts': 0,
            'problem_avg_score': 0,
            'problem_success_rate': 0,
            'video_views': 0,
            'late_night_ratio': 0,
            'weekend_ratio': 0,
            'activity_consistency': 0,
            'max_inactive_gap_days': 0
        }
        
        try:
            cursor = self.db_connection.cursor(dictionary=True)
            
            # Get video_progress count as proxy for video views
            cursor.execute("""
                SELECT COUNT(*) as video_views
                FROM video_progress
                WHERE user_id = %s AND course_id = %s
            """, (user_id, course_id))
            video_data = cursor.fetchone()
            if video_data:
                features['video_views'] = video_data['video_views']
            
            # Get h5p scores as proxy for problem attempts
            cursor.execute("""
                SELECT 
                    COUNT(*) as problem_attempts,
                    AVG(score_percentage) as problem_avg_score
                FROM h5p_scores
                WHERE user_id = %s AND course_id = %s
            """, (user_id, course_id))
            problem_data = cursor.fetchone()
            if problem_data:
                features['problem_attempts'] = problem_data['problem_attempts'] or 0
                features['problem_avg_score'] = round(problem_data['problem_avg_score'] or 0, 2)
                features['problem_success_rate'] = round(problem_data['problem_avg_score'] or 0, 2)
            
            # Calculate max inactive gap from mooc_progress
            if mooc_progress and mooc_progress.get('last_activity'):
                last_activity_dt = self.parse_datetime(str(mooc_progress['last_activity']))
                if last_activity_dt:
                    delta = datetime.now() - (last_activity_dt.replace(tzinfo=None) if last_activity_dt.tzinfo else last_activity_dt)
                    features['max_inactive_gap_days'] = delta.days
            
            cursor.close()
            
        except Exception as e:
            logger.error(f"Error calculating activity features: {e}")
        
        return features
    
    def calculate_derived_assessment_features(
        self,
        user_id: int,
        course_id: str
    ) -> Dict:
        """
        Calculate assessment-based features từ h5p_scores data
        """
        features = {
            'assessment_attempts_avg': 0,
            'assessment_improvement_rate': 0,
            'first_attempt_success_rate': 0,
            'struggling_assessments_count': 0
        }
        
        try:
            cursor = self.db_connection.cursor(dictionary=True)
            
            # Group by content_id to calculate per-assessment metrics
            cursor.execute("""
                SELECT 
                    content_id,
                    COUNT(*) as attempts,
                    MIN(score_percentage) as first_score,
                    MAX(score_percentage) as best_score
                FROM h5p_scores
                WHERE user_id = %s AND course_id = %s
                GROUP BY content_id
            """, (user_id, course_id))
            
            assessments = cursor.fetchall()
            
            if assessments:
                total_attempts = 0
                total_improvement = 0
                first_attempts_passed = 0
                struggling_count = 0
                
                for assessment in assessments:
                    attempts = assessment['attempts']
                    first_score = assessment['first_score'] or 0
                    best_score = assessment['best_score'] or 0
                    
                    total_attempts += attempts
                    
                    # Improvement rate
                    if first_score > 0:
                        improvement = ((best_score - first_score) / first_score) * 100
                        total_improvement += improvement
                    
                    # First attempt success
                    if first_score >= 60:  # Pass threshold
                        first_attempts_passed += 1
                    
                    # Struggling (nhiều attempts, score thấp)
                    if attempts > 2 and best_score < 60:
                        struggling_count += 1
                
                num_assessments = len(assessments)
                features['assessment_attempts_avg'] = round(total_attempts / num_assessments, 2)
                features['assessment_improvement_rate'] = round(total_improvement / num_assessments, 2)
                features['first_attempt_success_rate'] = round((first_attempts_passed / num_assessments) * 100, 2)
                features['struggling_assessments_count'] = struggling_count
            
            cursor.close()
            
        except Exception as e:
            logger.error(f"Error calculating assessment features: {e}")
        
        return features
    
    def calculate_derived_progress_features(
        self,
        user_id: int,
        course_id: str,
        mooc_progress: Optional[Dict] = None,
        enrollment_created: Optional[datetime] = None
    ) -> Dict:
        """
        Calculate progress-based features
        """
        features = {
            'progress_velocity': 0,
            'progress_acceleration': 0,
            'weeks_to_complete_estimate': None
        }
        
        try:
            if not mooc_progress or not enrollment_created:
                return features
            
            completion_rate = mooc_progress.get('completion_rate', 0)
            
            # Calculate weeks since enrollment
            delta = datetime.now() - (enrollment_created.replace(tzinfo=None) if enrollment_created.tzinfo else enrollment_created)
            weeks_enrolled = delta.days / 7.0
            
            if weeks_enrolled > 0:
                # Velocity: % completion per week
                velocity = completion_rate / weeks_enrolled
                features['progress_velocity'] = round(velocity, 2)
                
                # Estimate weeks to complete
                if velocity > 0:
                    remaining = 100 - completion_rate
                    weeks_estimate = remaining / velocity
                    features['weeks_to_complete_estimate'] = round(weeks_estimate, 2)
            
        except Exception as e:
            logger.error(f"Error calculating progress features: {e}")
        
        return features
