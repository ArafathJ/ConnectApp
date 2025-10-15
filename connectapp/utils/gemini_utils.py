import os
import google.generativeai as genai
from datetime import datetime
from typing import Dict, List, Optional
import json

class GeminiAPI:
    """Modular Gemini API integration for generating daily social challenges."""
    
    def __init__(self):
        """Initialize the Gemini API client."""
        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable is required")
        
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-2.5-flash')
    
    def generate_daily_task(self, user_progress: Dict) -> Dict:
        """
        Generate a daily social challenge based on user's past completion data.
        
        Args:
            user_progress: Dictionary containing user's progress data including:
                - completed_tasks: List of completed tasks
                - difficulty_preference: User's preferred difficulty level
                - recent_activities: Recent social activities
                - success_rate: User's completion rate
        
        Returns:
            Dict with keys: task_text, difficulty, created_at
        """
        try:
            # Extract user progress data
            completed_tasks = user_progress.get('completed_tasks', [])
            difficulty_preference = user_progress.get('difficulty_preference', 'medium')
            recent_activities = user_progress.get('recent_activities', [])
            success_rate = user_progress.get('success_rate', 0.5)
            
            # Determine difficulty level based on user progress
            difficulty = self._determine_difficulty(difficulty_preference, success_rate, completed_tasks)
            
            # Create context for the AI prompt
            context = self._build_context(completed_tasks, recent_activities, difficulty)
            
            # Generate the task using Gemini
            prompt = self._create_prompt(context, difficulty)
            response = self.model.generate_content(prompt)
            
            # Parse the response
            task_data = self._parse_response(response.text, difficulty)
            
            return {
                'task_text': task_data['task_text'],
                'difficulty': difficulty,
                'created_at': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            # Fallback to a default task if Gemini fails
            return self._get_fallback_task()
    
    def _determine_difficulty(self, preference: str, success_rate: float, completed_tasks: List) -> str:
        """Determine the appropriate difficulty level based on user progress."""
        # If user has high success rate and many completed tasks, suggest harder challenges
        if success_rate > 0.8 and len(completed_tasks) > 10:
            if preference == 'easy':
                return 'medium'
            elif preference == 'medium':
                return 'hard'
            else:
                return 'hard'
        
        # If user has low success rate, suggest easier challenges
        elif success_rate < 0.3:
            return 'easy'
        
        # Otherwise, use their preference
        return preference if preference in ['easy', 'medium', 'hard'] else 'medium'
    
    def _build_context(self, completed_tasks: List, recent_activities: List, difficulty: str) -> str:
        """Build context string for the AI prompt."""
        context_parts = []
        
        if completed_tasks:
            context_parts.append(f"User has completed {len(completed_tasks)} tasks recently.")
            context_parts.append("Recent completed tasks:")
            for task in completed_tasks[-5:]:  # Last 5 tasks
                context_parts.append(f"- {task}")
        
        if recent_activities:
            context_parts.append("Recent social activities:")
            for activity in recent_activities[-3:]:  # Last 3 activities
                context_parts.append(f"- {activity}")
        
        context_parts.append(f"Difficulty level: {difficulty}")
        
        return "\n".join(context_parts)
    
    def _create_prompt(self, context: str, difficulty: str) -> str:
        """Create the prompt for Gemini to generate a social challenge."""
        difficulty_descriptions = {
            'easy': 'simple, low-pressure social interactions that build confidence',
            'medium': 'moderate social challenges that require some effort but are achievable',
            'hard': 'challenging social tasks that push comfort zones and build strong connections'
        }
        
        prompt = f"""
You are a social connection coach helping users build meaningful relationships through daily challenges.

Context about the user:
{context}

Generate ONE specific, actionable social challenge for today that is {difficulty_descriptions.get(difficulty, 'moderate')}.

Requirements:
- Make it specific and actionable (not vague)
- Focus on building genuine connections with others
- Be encouraging and positive
- Keep it to 1-2 sentences maximum
- Make it something that can be completed in one day
- Avoid repetitive or generic challenges

Examples of good challenges:
- "Ask a colleague about their weekend plans and share one of your own"
- "Compliment someone on their work and ask them about their process"
- "Start a conversation with someone in line at a coffee shop"

Respond with ONLY the challenge text, no additional formatting or explanation.
"""
        return prompt
    
    def _parse_response(self, response_text: str, difficulty: str) -> Dict:
        """Parse the Gemini response and extract the task."""
        # Clean up the response
        task_text = response_text.strip()
        
        # Remove any quotes or extra formatting
        if task_text.startswith('"') and task_text.endswith('"'):
            task_text = task_text[1:-1]
        
        # Ensure it's not empty
        if not task_text or len(task_text) < 10:
            return self._get_fallback_task()
        
        return {
            'task_text': task_text,
            'difficulty': difficulty
        }
    
    def _get_fallback_task(self) -> Dict:
        """Provide a fallback task if Gemini fails."""
        fallback_tasks = {
            'easy': "Say hello and smile at three people today.",
            'medium': "Start a conversation with someone new and learn one interesting fact about them.",
            'hard': "Introduce yourself to someone you've never talked to and find a common interest."
        }
        
        return {
            'task_text': fallback_tasks.get('medium', "Make a genuine connection with someone today."),
            'difficulty': 'medium',
            'created_at': datetime.utcnow().isoformat()
        }


def generate_daily_task(user_progress: Dict) -> Dict:
    """
    Main function to generate a daily task using Gemini API.
    
    Args:
        user_progress: Dictionary containing user's progress data
        
    Returns:
        Dict with task_text, difficulty, and created_at
    """
    try:
        gemini = GeminiAPI()
        return gemini.generate_daily_task(user_progress)
    except Exception as e:
        # Return fallback task if anything fails
        return {
            'task_text': "Make a genuine connection with someone today.",
            'difficulty': 'medium',
            'created_at': datetime.utcnow().isoformat()
        }
