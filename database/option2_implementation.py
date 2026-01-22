"""
Option 2 Implementation: Advanced Stats APIs with Comparative Features
Add these methods to MOOCH5PDataFetcher class in fetch_mooc_h5p_data.py

Insert these methods before aggregate_raw_data (around line 927)
"""

    # ==================== OPTION 2: ADVANCED STATS APIs ====================
    
    def fetch_and_store_course_benchmarks(self, course_id: str) -> bool:
        """
        Fetch all Advanced Stats APIs and store course-level benchmarks
        This enables comparative features for Option 2
        """
        try:
            logger.info("Fetching course-level benchmarks from Advanced Stats APIs...")
            
            # Fetch Activity Stats
            activity_stats = self.fetch_activity_stats_summary(course_id)
            assessment_stats = self.fetch_assessment_stats_summary(course_id)
            progress_stats = self.fetch_progress_stats_summary(course_id)
            
            # Extract benchmarks
            benchmarks = {
                'course_id': course_id,
                'activity_avg_score': 0,
                'activity_total_activities': 0,
                'activity_avg_per_user': 0,
                'assessment_avg_score': 0,
                'assessment_avg_attempts': 0,
                'assessment_pass_rate': 0,
                'progress_avg_completion': 0,
                'progress_median_completion': 0,
                'progress_completion_rate': 0,
                'video_avg_completion': 0,
                'video_avg_watch_time': 0,
                'discussion_avg_interactions': 0,
                'discussion_participation_rate': 0,
                'total_students': 0,
                'active_students': 0
            }
            
            # Parse Activity Stats
            if activity_stats and activity_stats.get('success'):
                summary = activity_stats.get('summary', {})
                benchmarks['activity_avg_score'] = summary.get('avg_score', 0)
                benchmarks['activity_total_activities'] = summary.get('total_activities', 0)
                benchmarks['active_students'] = summary.get('total_active_users', 0)
                if benchmarks['active_students'] > 0:
                    benchmarks['activity_avg_per_user'] = round(
                        benchmarks['activity_total_activities'] / benchmarks['active_students'], 2
                    )
            
            # Parse Assessment Stats
            if assessment_stats and assessment_stats.get('success'):
                summary = assessment_stats.get('summary', {})
                benchmarks['assessment_avg_score'] = summary.get('avg_score', 0)
                benchmarks['total_students'] = summary.get('unique_students', 0)
                total_attempts = summary.get('total_attempts', 0)
                if benchmarks['total_students'] > 0:
                    benchmarks['assessment_avg_attempts'] = round(
                        total_attempts / benchmarks['total_students'], 2
                    )
            
            # Parse Progress Stats
            if progress_stats and progress_stats.get('success'):
                summary = progress_stats.get('summary', {})
                benchmarks['progress_avg_completion'] = summary.get('avg_progress', 0)
                benchmarks['progress_completion_rate'] = summary.get('completion_rate', 0)
                benchmarks['total_students'] = max(
                    benchmarks['total_students'], 
                    summary.get('total_students', 0)
                )
            
            # Store benchmarks to database
            cursor = self.db_connection.cursor()
            
            insert_query = """
            INSERT INTO course_stats_benchmarks (
                course_id, 
                activity_avg_score, activity_total_activities, activity_avg_per_user,
                assessment_avg_score, assessment_avg_attempts, assessment_pass_rate,
                progress_avg_completion, progress_median_completion, progress_completion_rate,
                video_avg_completion, video_avg_watch_time,
                discussion_avg_interactions, discussion_participation_rate,
                total_students, active_students
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
            ON DUPLICATE KEY UPDATE
                activity_avg_score = VALUES(activity_avg_score),
                activity_total_activities = VALUES(activity_total_activities),
                activity_avg_per_user = VALUES(activity_avg_per_user),
                assessment_avg_score = VALUES(assessment_avg_score),
                assessment_avg_attempts = VALUES(assessment_avg_attempts),
                progress_avg_completion = VALUES(progress_avg_completion),
                progress_completion_rate = VALUES(progress_completion_rate),
                total_students = VALUES(total_students),
                active_students = VALUES(active_students),
                updated_at = CURRENT_TIMESTAMP
            """
            
            values = (
                benchmarks['course_id'],
                benchmarks['activity_avg_score'],
                benchmarks['activity_total_activities'],
                benchmarks['activity_avg_per_user'],
                benchmarks['assessment_avg_score'],
                benchmarks['assessment_avg_attempts'],
                benchmarks['assessment_pass_rate'],
                benchmarks['progress_avg_completion'],
                benchmarks['progress_median_completion'],
                benchmarks['progress_completion_rate'],
                benchmarks['video_avg_completion'],
                benchmarks['video_avg_watch_time'],
                benchmarks['discussion_avg_interactions'],
                benchmarks['discussion_participation_rate'],
                benchmarks['total_students'],
                benchmarks['active_students']
            )
            
            cursor.execute(insert_query, values)
            self.db_connection.commit()
            cursor.close()
            
            logger.info(f"Course benchmarks stored: {benchmarks['total_students']} students, avg completion: {benchmarks['progress_avg_completion']:.2f}%")
            return True
            
        except Exception as e:
            logger.error(f"Error fetching/storing course benchmarks: {e}")
            if self.db_connection:
                self.db_connection.rollback()
            return False
    
    def fetch_activity_stats_summary(self, course_id: str) -> Optional[Dict]:
        """Fetch Activity Statistics from Advanced Stats API"""
        try:
            encoded_course_id = self.url_encode_course_id(course_id)
            url = f"{self.mooc_base_url}/stats/activity/{encoded_course_id}/"
            
            params = {'days': 90, 'group_by': 'day'}
            response = self.session.get(url, params=params, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    logger.info(f"Activity stats fetched")
                    return data
            else:
                logger.warning(f"Activity stats API returned {response.status_code}")
        except Exception as e:
            logger.error(f"Error fetching activity stats: {e}")
        return None
    
    def fetch_assessment_stats_summary(self, course_id: str) -> Optional[Dict]:
        """Fetch Assessment Statistics from Advanced Stats API"""
        try:
            encoded_course_id = self.url_encode_course_id(course_id)
            url = f"{self.mooc_base_url}/stats/assessment/{encoded_course_id}/"
            
            params = {'days': 90}
            response = self.session.get(url, params=params, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    logger.info(f"Assessment stats fetched")
                    return data
            else:
                logger.warning(f"Assessment stats API returned {response.status_code}")
        except Exception as e:
            logger.error(f"Error fetching assessment stats: {e}")
        return None
    
    def fetch_progress_stats_summary(self, course_id: str) -> Optional[Dict]:
        """Fetch Progress Statistics from Advanced Stats API"""
        try:
            encoded_course_id = self.url_encode_course_id(course_id)
            url = f"{self.mooc_base_url}/stats/progress/{encoded_course_id}/"
            
            params = {'days': 90}
            response = self.session.get(url, params=params, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    logger.info(f"Progress stats fetched")
                    return data
            else:
                logger.warning(f"Progress stats API returned {response.status_code}")
        except Exception as e:
            logger.error(f"Error fetching progress stats: {e}")
        return None
    
    def get_course_benchmarks(self, course_id: str) -> Optional[Dict]:
        """Retrieve course benchmarks from database"""
        try:
            cursor = self.db_connection.cursor(dictionary=True)
            cursor.execute("""
                SELECT * FROM course_stats_benchmarks
                WHERE course_id = %s
            """, (course_id,))
            benchmarks = cursor.fetchone()
            cursor.close()
            return benchmarks
        except Exception as e:
            logger.error(f"Error retrieving course benchmarks: {e}")
            return None
    
    def calculate_comparative_features(
        self, 
        user_metrics: Dict, 
        course_benchmarks: Dict
    ) -> Dict:
        """
        Calculate comparative features (Option 2)
        Compare user metrics against course benchmarks
        """
        features = {
            'relative_to_course_problem_score': 0,
            'relative_to_course_completion': 0,
            'relative_to_course_video_completion': 0,
            'relative_to_course_discussion': 0,
            'performance_percentile': 50,  # Default to median
            'is_below_course_average': 0,
            'is_top_performer': 0,
            'is_bottom_performer': 0
        }
        
        try:
            # Relative to course scores
            user_problem_score = user_metrics.get('problem_avg_score', 0)
            course_avg_problem = course_benchmarks.get('assessment_avg_score', 0)
            if course_avg_problem > 0:
                features['relative_to_course_problem_score'] = round(
                    user_problem_score - course_avg_problem, 2
                )
            
            # Relative completion
            user_completion = user_metrics.get('mooc_completion_rate', 0)
            course_avg_completion = course_benchmarks.get('progress_avg_completion', 0)
            if course_avg_completion > 0:
                features['relative_to_course_completion'] = round(
                    user_completion - course_avg_completion, 2
                )
            
            # Relative video completion
            user_video_completion = user_metrics.get('video_completion_rate', 0)
            course_avg_video = course_benchmarks.get('video_avg_completion', 0) or user_video_completion
            features['relative_to_course_video_completion'] = round(
                user_video_completion - course_avg_video, 2
            )
            
            # Relative discussion
            user_discussion = user_metrics.get('discussion_total_interactions', 0)
            course_avg_discussion = course_benchmarks.get('discussion_avg_interactions', 0)
            features['relative_to_course_discussion'] = int(
                user_discussion - course_avg_discussion
            )
            
            # Calculate composite performance score for percentile
            # Weighted: 40% completion, 30% problem score, 30% engagement
            user_score = (
                user_completion * 0.4 +
                user_problem_score * 0.3 +
                (user_video_completion + min(user_discussion * 2, 100)) / 2 * 0.3
            )
            
            course_avg_score = (
                course_avg_completion * 0.4 +
                course_avg_problem * 0.3 +
                course_avg_video * 0.3
            )
            
            # Estimate percentile based on deviation from mean
            # Simple heuristic: assume normal distribution
            if course_avg_score > 0:
                deviation = (user_score - course_avg_score) / course_avg_score
                # Map deviation to percentile (rough approximation)
                if deviation > 0.5:
                    percentile = 90  # Top 10%
                elif deviation > 0.25:
                    percentile = 75  # Top quartile
                elif deviation > 0:
                    percentile = 60  # Above average
                elif deviation > -0.25:
                    percentile = 40  # Below average
                elif deviation > -0.5:
                    percentile = 25  # Bottom quartile
                else:
                    percentile = 10  # Bottom 10%
                
                features['performance_percentile'] = percentile
            
            # Set flags
            features['is_below_course_average'] = 1 if user_score < course_avg_score else 0
            features['is_top_performer'] = 1 if features['performance_percentile'] >= 75 else 0
            features['is_bottom_performer'] = 1 if features['performance_percentile'] <= 25 else 0
            
        except Exception as e:
            logger.error(f"Error calculating comparative features: {e}")
        
        return features
