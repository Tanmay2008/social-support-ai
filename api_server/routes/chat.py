# 5_api_server/routes/chat.py
from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from typing import Dict, List, Optional, Any
import json
from datetime import datetime
import logging
import asyncio

from ai_agents.agent_framework import AgentState
from agent_orchestration.workflow_orchestrator import get_workflow

router = APIRouter()
logger = logging.getLogger(__name__)

# In-memory storage for chat sessions (use Redis in production)
chat_sessions = {}
workflow = get_workflow()

class ConnectionManager:
    """Manage WebSocket connections for real-time chat"""
    
    def __init__(self):
        self.active_connections: List[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
    
    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
    
    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)
    
    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)

manager = ConnectionManager()

@router.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """WebSocket endpoint for real-time chat"""
    await manager.connect(websocket)
    
    # Initialize session if not exists
    if session_id not in chat_sessions:
        chat_sessions[session_id] = {
            'messages': [],
            'created_at': datetime.now().isoformat(),
            'application_context': None
        }
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            message_data = json.loads(data)
            
            # Process message
            response = await _process_chat_message(session_id, message_data)
            
            # Send response back to client
            await manager.send_personal_message(
                json.dumps(response), 
                websocket
            )
            
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        logger.info(f"WebSocket disconnected for session {session_id}")

@router.post("/message")
async def send_chat_message(
    message: str,
    session_id: Optional[str] = None,
    application_id: Optional[str] = None
):
    """Send a chat message via HTTP (fallback for WebSocket)"""
    try:
        # Generate session ID if not provided
        if not session_id:
            session_id = f"CHAT{int(datetime.now().timestamp())}"
        
        message_data = {
            'message': message,
            'type': 'user',
            'timestamp': datetime.now().isoformat()
        }
        
        # Process message
        response = await _process_chat_message(session_id, message_data, application_id)
        
        return {
            "success": True,
            "session_id": session_id,
            "response": response,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Chat message processing failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Chat processing failed: {str(e)}")

@router.get("/sessions/{session_id}")
async def get_chat_session(session_id: str):
    """Get chat session history"""
    if session_id not in chat_sessions:
        raise HTTPException(status_code=404, detail="Chat session not found")
    
    return {
        "session_id": session_id,
        "messages": chat_sessions[session_id]['messages'],
        "created_at": chat_sessions[session_id]['created_at'],
        "application_context": chat_sessions[session_id]['application_context']
    }

@router.post("/sessions/{session_id}/context")
async def set_chat_context(session_id: str, context: Dict[str, Any]):
    """Set application context for chat session"""
    if session_id not in chat_sessions:
        chat_sessions[session_id] = {
            'messages': [],
            'created_at': datetime.now().isoformat(),
            'application_context': context
        }
    else:
        chat_sessions[session_id]['application_context'] = context
    
    return {
        "success": True,
        "session_id": session_id,
        "context_set": True,
        "timestamp": datetime.now().isoformat()
    }

@router.delete("/sessions/{session_id}")
async def delete_chat_session(session_id: str):
    """Delete a chat session"""
    if session_id in chat_sessions:
        del chat_sessions[session_id]
    
    return {
        "success": True,
        "session_id": session_id,
        "deleted": True,
        "timestamp": datetime.now().isoformat()
    }

async def _process_chat_message(session_id: str, message_data: Dict, application_id: Optional[str] = None) -> Dict:
    """Process incoming chat message and generate response"""
    try:
        # Initialize session if not exists
        if session_id not in chat_sessions:
            chat_sessions[session_id] = {
                'messages': [],
                'created_at': datetime.now().isoformat(),
                'application_context': {'application_id': application_id} if application_id else None
            }
        
        user_message = message_data.get('message', '')
        message_type = message_data.get('type', 'user')
        
        # Add user message to session history
        chat_sessions[session_id]['messages'].append({
            'type': 'user',
            'content': user_message,
            'timestamp': datetime.now().isoformat()
        })
        
        # Generate AI response based on message content and context
        ai_response = await _generate_ai_response(
            user_message, 
            chat_sessions[session_id]
        )
        
        # Add AI response to session history
        chat_sessions[session_id]['messages'].append({
            'type': 'assistant',
            'content': ai_response['response'],
            'suggestions': ai_response.get('suggestions', []),
            'timestamp': datetime.now().isoformat()
        })
        
        # Keep only last 50 messages to prevent memory issues
        if len(chat_sessions[session_id]['messages']) > 50:
            chat_sessions[session_id]['messages'] = chat_sessions[session_id]['messages'][-50:]
        
        return {
            'type': 'assistant',
            'response': ai_response['response'],
            'suggestions': ai_response.get('suggestions', []),
            'session_id': session_id,
            'timestamp': datetime.now().isoformat(),
            'message_count': len(chat_sessions[session_id]['messages'])
        }
        
    except Exception as e:
        logger.error(f"Chat message processing error: {str(e)}")
        return {
            'type': 'error',
            'response': "I apologize, but I'm experiencing technical difficulties. Please try again later.",
            'session_id': session_id,
            'timestamp': datetime.now().isoformat()
        }

async def _generate_ai_response(message: str, session: Dict) -> Dict:
    """Generate AI response based on message content and session context"""
    message_lower = message.lower()
    context = session.get('application_context', {})
    application_id = context.get('application_id')
    
    # Response templates for different types of queries
    if any(word in message_lower for word in ['status', 'progress', 'update']):
        return await _handle_status_query(application_id, message)
    
    elif any(word in message_lower for word in ['eligibility', 'qualify', 'requirements']):
        return await _handle_eligibility_query(message)
    
    elif any(word in message_lower for word in ['document', 'upload', 'submit']):
        return await _handle_document_query(message)
    
    elif any(word in message_lower for word in ['support', 'benefit', 'assistance']):
        return await _handle_support_query(message)
    
    elif any(word in message_lower for word in ['training', 'job', 'employment']):
        return await _handle_employment_query(message)
    
    elif any(word in message_lower for word in ['time', 'duration', 'how long']):
        return await _handle_timing_query(message)
    
    elif any(word in message_lower for word in ['appeal', 'reject', 'decline']):
        return await _handle_appeal_query(message)
    
    else:
        return await _handle_general_query(message, session)

async def _handle_status_query(application_id: Optional[str], message: str) -> Dict:
    """Handle application status queries"""
    if not application_id:
        response = "I can help you check your application status. Please provide your application ID, or if you've already submitted an application, make sure you've set the application context in our chat."
        suggestions = ["How do I find my application ID?", "How do I set application context?"]
    else:
        # In a real implementation, this would query the database
        response = f"For application {application_id}, I can see that it's currently being processed. The typical processing time is 2-3 minutes. Would you like me to check the detailed status?"
        suggestions = ["What's the current processing stage?", "When will I get the result?"]
    
    return {
        'response': response,
        'suggestions': suggestions
    }

async def _handle_eligibility_query(message: str) -> Dict:
    """Handle eligibility criteria queries"""
    response = """Eligibility for social support is determined based on multiple factors:

• **Income Level**: Monthly income and income per family member
• **Employment Status**: Current employment situation and history
• **Family Situation**: Number of dependents and family size
• **Financial Assets**: Total assets, liabilities, and net worth
• **Housing Situation**: Current housing type and costs

Our AI system automatically assesses all these factors to determine your eligibility score and appropriate support level."""

    suggestions = [
        "What income level qualifies for support?",
        "How does family size affect eligibility?",
        "What documents are needed for eligibility assessment?"
    ]
    
    return {
        'response': response,
        'suggestions': suggestions
    }

async def _handle_document_query(message: str) -> Dict:
    """Handle document-related queries"""
    response = """For a complete social support application, you typically need:

**Required Documents:**
• Emirates ID (copy)
• Recent bank statements (3 months)
• Proof of income (salary certificate or business records)
• Completed application form

**Additional Supporting Documents:**
• Resume/CV for employment assessment
• Assets and liabilities statement
• Credit report (optional but helpful)
• Rental agreement (if applicable)

Our system can process scanned documents and extract information automatically using AI."""

    suggestions = [
        "How do I upload documents?",
        "What file formats are supported?",
        "What if I'm missing some documents?"
    ]
    
    return {
        'response': response,
        'suggestions': suggestions
    }

async def _handle_support_query(message: str) -> Dict:
    """Handle support and benefits queries"""
    response = """The social support program offers several types of assistance:

**Financial Support:**
• Monthly living allowance based on need
• Emergency financial assistance
• Rental support subsidies

**Economic Enablement:**
• Job training and skills development
• Career counseling and job matching
• Entrepreneurship support programs
• Educational assistance

**Social Services:**
• Family counseling and support
• Healthcare access assistance
• Childcare support programs

The specific support you qualify for depends on your eligibility assessment results."""

    suggestions = [
        "What training programs are available?",
        "How much financial support can I get?",
        "What is economic enablement?"
    ]
    
    return {
        'response': response,
        'suggestions': suggestions
    }

async def _handle_employment_query(message: str) -> Dict:
    """Handle employment and training queries"""
    response = """We offer comprehensive employment support services:

**Training Programs:**
• Digital literacy and computer skills
• Customer service certification
• Healthcare assistant training
• Technical and vocational skills
• Language and communication skills

**Employment Services:**
• Job matching with local employers
• Resume writing and interview preparation
• Career counseling and assessment
• Internship and apprenticeship programs

**Entrepreneurship Support:**
• Small business startup training
• Micro-enterprise development
• Business planning assistance
• Access to startup grants

These services are designed to help you gain employment or improve your current situation."""

    suggestions = [
        "How do I apply for training programs?",
        "What jobs are available through your program?",
        "Do you offer paid internships?"
    ]
    
    return {
        'response': response,
        'suggestions': suggestions
    }

async def _handle_timing_query(message: str) -> Dict:
    """Handle timing and process duration queries"""
    response = """Here are the typical timeframes for our processes:

**Application Processing:**
• Initial review: 2-3 minutes (AI automated)
• Complete assessment: 5-10 minutes
• Final decision: Within 24 hours

**Support Services:**
• Training program start: 1-4 weeks after approval
• Job matching: 2-6 weeks based on your profile
• Financial support: First payment within 1 week of approval

**Document Processing:**
• Document verification: 1-2 business days
• Additional information requests: 24-48 hour response time

We strive to make the process as fast and efficient as possible using AI automation."""

    suggestions = [
        "How can I speed up my application?",
        "What's the current processing time?",
        "When will I receive my first payment?"
    ]
    
    return {
        'response': response,
        'suggestions': suggestions
    }

async def _handle_appeal_query(message: str) -> Dict:
    """Handle appeal and reconsideration queries"""
    response = """If your application was declined or you disagree with the decision:

**Appeal Process:**
1. Request a detailed explanation of the decision
2. Submit additional supporting documents
3. Request a manual review by a case officer
4. Appeal to the social support committee

**Common Reasons for Appeal:**
• New financial circumstances
• Additional documentation available
• Special circumstances not initially considered
• Errors in initial assessment

**Next Steps:**
• Contact our support team within 30 days of decision
• Provide any new relevant information
• Be prepared to discuss your situation in detail

We're committed to fair and transparent decision-making."""

    suggestions = [
        "How do I start an appeal?",
        "What documents help in appeals?",
        "What is the success rate of appeals?"
    ]
    
    return {
        'response': response,
        'suggestions': suggestions
    }

async def _handle_general_query(message: str, session: Dict) -> Dict:
    """Handle general information queries"""
    response = """I'm here to help you with your social support application and questions about economic enablement programs.

I can assist you with:
• Application status and progress updates
• Eligibility criteria and requirements
• Document submission and verification
• Support services and benefits information
• Training and employment opportunities
• Appeal processes and decision reviews

Please feel free to ask me anything about the social support program, or if you have a specific application, provide your application ID for more personalized assistance."""

    suggestions = [
        "How do I check my application status?",
        "What documents do I need to apply?",
        "What types of support are available?",
        "How long does the process take?"
    ]
    
    return {
        'response': response,
        'suggestions': suggestions
    }