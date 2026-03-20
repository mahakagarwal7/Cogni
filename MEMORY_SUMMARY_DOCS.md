# Memory Summary Feature

## Overview

The Memory Summary feature allows users to generate intelligent summaries of their conversations and export them as PDF documents. This helps users review their learning progress and consolidate key insights.

## Features

✨ **Conversation Summarization**

- Automatically chunks long conversations for better processing
- Extracts key learning points and insights
- Generates both quick previews and detailed full summaries
- Uses LLM-powered synthesis for intelligent summarization

📥 **PDF Export**

- Professional PDF formatting with proper styling
- Timestamp and footer information
- Automatic fallback system for PDF libraries
- Single-click download from the UI

## Architecture

### Frontend Components (`src/app/page.tsx`)

1. **Memory Feature Tab**
   - Located in the feature navigation sidebar
   - Displays icon: `<MagicWandIcon />`
   - Description: "View what you remember"

2. **Summary Generation Button**
   - Located in the footer when Memory tab is active
   - Triggered by `generateSummary()` function
   - Shows spinner during generation
   - Disabled when conversation is empty

3. **PDF Download Button**
   - Appears after summary is generated
   - Triggered by `downloadSummaryPDF()` function
   - Downloads file as `learning_summary.pdf`

### Backend Services

#### `/memory/summary` - POST Endpoint

**Request:**

```json
{
  "conversation": "Full conversation text..."
}
```

**Response:**

```json
{
  "status": "success",
  "data": {
    "preview": "First 2 paragraphs of summary...",
    "full_summary": "Complete structured summary...",
    "demo_mode": false
  }
}
```

#### `/memory/summary/pdf` - POST Endpoint

**Request:**

```json
{
  "summary_text": "Full summary text to convert to PDF..."
}
```

**Response:**

- Binary PDF file
- Content-Type: `application/pdf`
- Disposition: `attachment; filename=learning_summary.pdf`

### Summary Service (`app/services/summary_service.py`)

**Key Methods:**

1. **`async generate_summary(conversation_text)`**
   - Main entry point
   - Chunks conversation for processing
   - Summarizes each chunk
   - Synthesizes final summary
   - Extracts preview

2. **`_chunk_text(text, chunk_size)`**
   - Splits text into manageable chunks
   - Respects sentence boundaries
   - Default chunk size: 500 characters

3. **`async _summarize_chunks(chunks)`**
   - Processes each chunk with LLM
   - Cleans output to remove meta-text
   - Returns list of partial summaries

4. **`async _generate_final_summary(combined_text)`**
   - Creates structured final summary
   - 4-6 paragraphs covering:
     - Learning overview
     - Key topics/concepts
     - Progress and achievements
     - Challenges and insights
     - Recommendations
     - Next steps

5. **`generate_pdf(summary, title)`**
   - Converts summary to PDF
   - Uses reportlab (primary) or fpdf2 (fallback)
   - Professional formatting
   - Timestamp footer

## Usage Flow

### From Frontend

1. User clicks on **Memory** feature tab
2. View shows previous conversation messages (read-only)
3. Click **"Generate Summary"** button
4. UI shows loading spinner
5. Summary is generated and displayed in chat
6. **"Download PDF"** button becomes available
7. Click to download summary as PDF file

### API Integration

```typescript
// In frontend api.ts
async generateSummary(conversation: string): Promise<APIResponse> {
  const res = await fetch(`${API_URL}/memory/summary`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ conversation })
  });
  return res.json();
}

async downloadSummaryPDF(summaryText: string): Promise<Blob> {
  const res = await fetch(`${API_URL}/memory/summary/pdf`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ summary_text: summaryText })
  });
  return res.blob();
}
```

## Configuration

### Requirements

Add these Python packages to `requirements.txt`:

```
reportlab>=4.0.0  # Primary PDF generation
fpdf2>=2.7.0      # Fallback PDF generation
```

### Environment

No special environment variables needed. The service uses:

- `LLM_SERVICE` for summary generation
- Local file system for temporary PDF operations

## Error Handling

### Summary Generation Failures

- Returns fallback message: "Summary unavailable. Try again."
- Logs error for debugging
- Sets `demo_mode: true` for frontend error indication

### PDF Generation Failures

- Tries reportlab first
- Falls back to fpdf2
- Final fallback: returns plaintext (user can save as .txt)

### Network Issues

- Frontend detects backend connection errors
- Shows error message in chat
- User can retry the operation

## Performance Considerations

### Chunking Strategy

- Default chunk size: 500 characters
- Avoids processing massive conversations at once
- Enables partial processing and fallback

### LLM Calls

- Temperature: 0.5-0.6 for balanced creativity/accuracy
- Max tokens: 150 (chunks), 800 (final summary)
- Request timeout: 30 seconds

### PDF Generation

- In-memory processing (BytesIO)
- No disk writes except for downloads
- Efficient fallback chain

## Testing

### Backend Service Tests

```bash
# Test summary service directly
python test_summary_feature.py
```

### API Endpoint Tests

```bash
# Test HTTP endpoints
# Make sure backend is running first
python test_api_summary.py
```

### Manual Testing

1. Start backend: `python run.py`
2. Start frontend: `npm run dev`
3. Generate a conversation across features
4. Switch to Memory tab
5. Click "Generate Summary"
6. Verify summary appears
7. Click "Download PDF"
8. Verify PDF downloads

## Files Modified

### Backend

- `app/routes/memory_routes.py` - Added request models, fixed endpoint handlers
- `app/services/summary_service.py` - Implemented summarization logic
- `requirements.txt` - Added PDF dependencies

### Frontend

- `src/app/page.tsx` - Added memory feature UI with buttons
- `src/services/api.ts` - Added summary API methods (already present)

### New Test Files

- `test_summary_feature.py` - Service level tests
- `test_api_summary.py` - Integration tests

## Future Enhancements

1. **Filtering Options**
   - Summarize only specific features
   - Date range summaries
   - Topic-based summaries

2. **Advanced Exports**
   - Markdown export
   - JSON export with structured data
   - Email delivery of summaries

3. **Enhanced Analysis**
   - Sentiment analysis of learning journey
   - Skill progression tracking
   - Learning pattern identification

4. **Customization**
   - User-selected summary length
   - Custom PDF themes/branding
   - Section selection for summary

## Troubleshooting

### PDF Generation Fails

- Ensure reportlab/fpdf2 are installed: `pip install -r requirements.txt`
- Check available disk space
- Try fallback text download

### Summary Not Generating

- Check backend is running
- Ensure conversation has content
- Check browser console for errors
- Review backend logs

### Download Doesn't Start

- Check browser download settings
- Verify PDF file size (should be > 100 bytes)
- Try different browser
- Check CORS configuration

## Support

For issues or feature requests related to the Memory Summary feature:

1. Check the test files for examples
2. Review backend logs for detailed errors
3. Check frontend console (F12) for client errors
