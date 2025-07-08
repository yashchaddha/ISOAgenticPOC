
# ISO 27001 Agentic Audit System

A comprehensive ISO 27001 audit system built with FastAPI and LangGraph, featuring an intelligent agent that guides users through the audit process.

## Features

### 🤖 Agentic Audit System
- **Intelligent Workflow**: LangGraph-based agent that orchestrates the entire audit process
- **Conversational Interface**: Natural language queries and responses
- **Document Analysis**: Upload and analyze documents for compliance
- **Automated Scoring**: Calculate compliance scores and generate recommendations
- **State Management**: Persistent audit sessions with conversation history

### 📋 Traditional Audit System
- **Clause-by-Clause Auditing**: Systematic review of ISO 27001 clauses
- **Session Management**: Track audit progress across multiple sessions
- **Response Recording**: Store and manage audit responses

### 📁 Document Management
- **S3 Integration**: Secure document upload and storage
- **Presigned URLs**: Direct upload to S3 for better performance
- **Document Analysis**: AI-powered compliance checking

## Architecture

### Graph Nodes
The agentic system consists of the following nodes:

1. **Initialize Session**: Set up new audit session
2. **Get Current Clause**: Retrieve current clause information
3. **Process User Query**: Handle natural language questions
4. **Record User Answer**: Store responses and advance
5. **Analyze Documents**: Check uploaded documents for compliance
6. **Advance to Next Clause**: Move to next audit item
7. **Calculate Compliance Score**: Compute overall compliance
8. **Generate Recommendations**: Create actionable recommendations
9. **Create Audit Report**: Generate final comprehensive report

### Tools
The agent has access to specialized tools:

- **GetCurrentClauseTool**: Retrieve current clause metadata
- **RecordAnswerTool**: Save responses and advance progress
- **AnalyzeDocumentTool**: Check documents for compliance
- **CalculateComplianceScoreTool**: Compute compliance metrics
- **GenerateRecommendationsTool**: Create improvement suggestions

## API Endpoints

### Agentic System (`/agent`)
- `POST /agent/start` - Start new agentic audit session
- `POST /agent/{session_id}/query` - Ask questions about current clause
- `POST /agent/{session_id}/answer` - Record answers for current clause
- `GET /agent/{session_id}/status` - Get audit session status
- `POST /agent/{session_id}/upload-document` - Add document for analysis
- `GET /agent/{session_id}/report` - Get final audit report
- `GET /agent/{session_id}/conversation` - Get conversation history
- `POST /agent/{session_id}/complete` - Manually complete audit

### Traditional System (`/audit`)
- `POST /audit/start` - Start traditional audit session
- `GET /audit/{session_id}/next` - Get next clause
- `POST /audit/{session_id}/query` - Query about current clause
- `POST /audit/{session_id}/answer` - Record answer

### Document Management (`/upload`)
- `POST /upload/presign` - Get presigned upload URL
- `POST /upload/complete` - Complete document upload
- `GET /upload/all` - List all uploaded documents

## Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd iso27001-agent
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

4. **Run the application**
   ```bash
   uvicorn app.main:app --reload
   ```

## Environment Variables

```env
OPENAI_API_KEY=your_openai_api_key
MONGODB_URI=your_mongodb_connection_string
S3_BUCKET=your_s3_bucket_name
AWS_REGION=your_aws_region
```

## Usage Examples

### Starting an Agentic Audit
```bash
curl -X POST "http://localhost:8000/agent/start" \
  -H "Content-Type: application/json"
```

### Asking Questions
```bash
curl -X POST "http://localhost:8000/agent/{session_id}/query" \
  -H "Content-Type: application/json" \
  -d '{"query": "What does this clause require us to implement?"}'
```

### Recording Answers
```bash
curl -X POST "http://localhost:8000/agent/{session_id}/answer" \
  -H "Content-Type: application/json" \
  -d '{"answer": "Yes, we have implemented this requirement"}'
```

### Uploading Documents
```bash
curl -X POST "http://localhost:8000/agent/{session_id}/upload-document" \
  -H "Content-Type: application/json" \
  -d '{"document_key": "policy-document.pdf"}'
```

### Getting Final Report
```bash
curl -X GET "http://localhost:8000/agent/{session_id}/report"
```

## State Management

The system uses LangGraph's state management to maintain:

- **Session Information**: Session ID, creation time, status
- **Audit Progress**: Current clause, total clauses, completion status
- **User Responses**: All recorded answers with timestamps
- **Conversation History**: Complete chat history with the agent
- **Document Analysis**: Results from document compliance checks
- **Compliance Metrics**: Scores, recommendations, and findings

## Workflow

1. **Session Initialization**: Create new audit session with unique ID
2. **Clause Navigation**: Agent guides through each ISO 27001 clause
3. **Interactive Q&A**: Users can ask questions and get expert guidance
4. **Document Analysis**: Upload relevant documents for compliance checking
5. **Answer Recording**: Record responses for each clause
6. **Progress Tracking**: Monitor completion status and compliance scores
7. **Report Generation**: Generate comprehensive final audit report

## Development

### Adding New Clauses
Edit `app/services/audit_engine.py` to add new clauses to `CLAUSE_METADATA`:

```python
{
    "question": "Clause X.X: Your question here?",
    "description": "Detailed description of the clause requirements",
    "attributes": ["Attribute 1", "Attribute 2", "Attribute 3"]
}
```

### Extending Tools
Add new tools in `app/agents/tools.py` and register them in `AUDIT_TOOLS`.

### Customizing Nodes
Modify node behavior in `app/agents/nodes.py` to change how the agent processes information.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

[Your License Here]
