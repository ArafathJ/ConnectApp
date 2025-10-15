# Gemini API Integration for Daily Tasks

This document explains the new Gemini API integration for generating personalized daily social challenges.

## Overview

The integration allows the app to generate unique, personalized daily social challenges using Google's Gemini AI model based on each user's progress and completion history.

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Set Environment Variable

You need a Gemini API key from Google AI Studio:

```bash
# Windows
set GEMINI_API_KEY=your_api_key_here

# Linux/Mac
export GEMINI_API_KEY=your_api_key_here
```

### 3. Database Migration

The `DailyTask` model has been updated with new fields:
- `difficulty`: "easy", "medium", or "hard"
- `created_at`: Timestamp when the task was created

Run a database migration to update existing databases.

## API Endpoint

### GET/POST `/api/daily_task`

Generates a new daily task for the authenticated user.

**Response:**
```json
{
  "success": true,
  "task": {
    "id": 123,
    "task_text": "Ask a colleague about their weekend plans and share one of your own",
    "difficulty": "medium",
    "created_at": "2024-01-15T10:30:00.000Z",
    "completed": false,
    "xp_points": 10
  }
}
```

**Error Response:**
```json
{
  "success": false,
  "error": "Failed to generate daily task",
  "message": "Error details here"
}
```

## How It Works

### 1. User Progress Analysis

The system analyzes the user's:
- Completed tasks from the last 30 days
- Success rate (completion percentage)
- Recent social activities
- Current score

### 2. Difficulty Determination

The AI determines difficulty based on:
- **Easy**: Low success rate (< 30%) or user preference
- **Medium**: Default difficulty or moderate success rate
- **Hard**: High success rate (> 80%) and many completed tasks

### 3. Task Generation

Gemini generates personalized challenges that:
- Are specific and actionable
- Build genuine connections
- Match the user's difficulty level
- Avoid repetitive tasks
- Can be completed in one day

### 4. Fallback System

If the Gemini API fails, the system provides fallback tasks:
- Easy: "Say hello and smile at three people today."
- Medium: "Start a conversation with someone new and learn one interesting fact about them."
- Hard: "Introduce yourself to someone you've never talked to and find a common interest."

## Usage in Frontend

```javascript
// Fetch a new daily task
fetch('/api/daily_task', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
    }
})
.then(response => response.json())
.then(data => {
    if (data.success) {
        // Display the new task
        document.getElementById('task-text').textContent = data.task.task_text;
        document.getElementById('task-difficulty').textContent = data.task.difficulty;
    } else {
        console.error('Failed to generate task:', data.error);
    }
});
```

## Testing

Run the test script to verify the integration:

```bash
python test_gemini_integration.py
```

This will test both normal operation and fallback behavior.

## Error Handling

The integration includes comprehensive error handling:
- API key validation
- Network timeouts
- Invalid responses
- Database errors
- Fallback to default tasks

## Customization

You can customize the AI prompts by modifying the `_create_prompt()` method in `connectapp/utils/gemini_utils.py`.

## Security Notes

- API keys should be stored securely as environment variables
- The integration includes rate limiting through Gemini's API limits
- User data is only sent to Gemini for task generation, not stored
- All database operations use parameterized queries to prevent SQL injection
