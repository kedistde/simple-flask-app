from flask import Flask, request, jsonify
from flask_restx import Api, Resource, fields
from celery import Celery
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Create Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key')

# Configure Celery
celery = Celery(
    __name__,
    broker=os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0'),
    backend=os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')
)

# Configure Swagger
api = Api(
    app,
    version='1.0',
    title='Simple Flask API',
    description='A simple Flask API with Celery and Swagger',
    doc='/swagger/'
)

# Namespace for API
ns = api.namespace('api', description='API operations')

# Models for Swagger
email_model = api.model('Email', {
    'to': fields.String(required=True, description='Recipient email'),
    'subject': fields.String(required=True, description='Email subject'),
    'message': fields.String(required=True, description='Email message')
})

task_model = api.model('Task', {
    'name': fields.String(required=True, description='Task name'),
    'duration': fields.Integer(description='Task duration in seconds', default=5)
})

# Celery task - simulate sending email
@celery.task
def send_email_async(to, subject, message):
    """Simulate sending an email (in real app, use Flask-Mail or similar)"""
    print(f"📧 Sending email to: {to}")
    print(f"📋 Subject: {subject}")
    print(f"📝 Message: {message}")
    # Simulate some work
    import time
    time.sleep(3)
    return f"Email sent to {to} successfully!"

# Celery task - simulate long running task
@celery.task
def long_running_task_async(task_name, duration=5):
    """Simulate a long running task"""
    print(f"🚀 Starting task: {task_name}")
    print(f"⏰ Duration: {duration} seconds")
    import time
    for i in range(duration):
        print(f"⏳ Task {task_name}: {i+1}/{duration}")
        time.sleep(1)
    print(f"✅ Task {task_name} completed!")
    return f"Task {task_name} completed in {duration} seconds"

# API Routes
@ns.route('/health')
class HealthCheck(Resource):
    def get(self):
        """Health check endpoint"""
        return {'status': 'healthy', 'message': 'API is running!'}

@ns.route('/send-email')
class SendEmail(Resource):
    @ns.expect(email_model)
    def post(self):
        """Send email asynchronously"""
        data = request.get_json()
        task = send_email_async.delay(
            data['to'], 
            data['subject'], 
            data['message']
        )
        return {
            'message': 'Email task started',
            'task_id': task.id
        }, 202

@ns.route('/start-task')
class StartTask(Resource):
    @ns.expect(task_model)
    def post(self):
        """Start a long running task"""
        data = request.get_json()
        task = long_running_task_async.delay(
            data['name'],
            data.get('duration', 5)
        )
        return {
            'message': 'Task started',
            'task_id': task.id
        }, 202

@ns.route('/task-status/<task_id>')
class TaskStatus(Resource):
    def get(self, task_id):
        """Check task status"""
        task = long_running_task_async.AsyncResult(task_id)
        return {
            'task_id': task_id,
            'status': task.status,
            'result': task.result
        }

@ns.route('/test')
class TestEndpoint(Resource):
    def get(self):
        """Test endpoint that returns simple data"""
        return {
            'message': 'Hello from Flask!',
            'endpoints': [
                '/api/health',
                '/api/send-email',
                '/api/start-task',
                '/api/task-status/<task_id>'
            ]
        }

# Basic route
@app.route('/')
def home():
    return '''
    <h1>Simple Flask App</h1>
    <p>API is running!</p>
    <p>Check <a href="/swagger/">Swagger Documentation</a></p>
    <p>Endpoints:</p>
    <ul>
        <li>GET /api/health</li>
        <li>POST /api/send-email</li>
        <li>POST /api/start-task</li>
        <li>GET /api/task-status/{task_id}</li>
    </ul>
    '''

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
