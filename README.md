# Personal Event Finding AI Agent

A Python-based AI agent that uses OpenAI's Responses API with web search to find London-based events matching your interests, automatically deduplicating and logging new events to a CSV file.

## Features

- 🔍 **Web Search Integration**: Uses OpenAI's `web_search_preview` tool for real-time event discovery
- 🎯 **Smart Filtering**: Focuses on London-based events matching your specified interests
- 🚫 **Deduplication**: Automatically avoids logging duplicate events using hash and URL matching
- 📊 **CSV Logging**: Maintains a persistent log of all discovered events
- 🔄 **Batch Processing**: Processes multiple search queries in one run
- 💬 **Interactive Mode**: CLI interface for real-time event searching and query management

## Project Structure

```
ai_agent/
├── main.py              # Main script and interactive mode
├── config.py            # Configuration and settings
├── openai_client.py     # OpenAI API integration
├── query_loader.py      # Query management
├── event_parser.py      # Response parsing and validation
├── memory.py            # Event storage and deduplication
├── requirements.txt     # Python dependencies
├── .env.example         # Environment variables template
├── queries.txt          # Search queries (auto-generated)
└── events_log.csv       # Event database (auto-generated)
```

## Setup

1. **Clone and navigate to the project:**
   ```bash
   cd ai_agent
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables:**
   ```bash
   cp .env.example .env
   # Edit .env and add your OpenAI API key
   ```

4. **Get your OpenAI API key:**
   - Visit [OpenAI API Keys](https://platform.openai.com/api-keys)
   - Create a new API key
   - Add it to your `.env` file

## Usage

### Basic Event Search

Run the main script to search for events using all queries in `queries.txt`:

```bash
python main.py
```

The script will:
1. Load search queries from `queries.txt`
2. Search for events using OpenAI's web search
3. Parse and validate event data
4. Log new events to `events_log.csv` (skipping duplicates)
5. Display a summary of results

### Interactive Mode

For real-time searching and query management:

```bash
python main.py --interactive
```

Available commands:
- `search` - Search for events with a custom query
- `add` - Add a new search query to queries.txt
- `list` - Show all current search queries
- `summary` - Display event database statistics
- `find` - Search existing events in the database
- `quit` - Exit interactive mode

### Managing Search Queries

Edit `queries.txt` to customize your event interests. **No need to specify time periods** - the system automatically searches for upcoming/future events:

```
# Event search queries - one per line
# Lines starting with # are comments
# The system automatically searches for upcoming/future events

London hackathon
Half marathon London
Climate networking London
Product design conference London
Tech meetup London
Startup networking event London
AI conference London
Web3 blockchain event London
Data science meetup London
```

The system will automatically:
- Add "upcoming" to queries that don't already specify timeframes
- Focus searches on future events only
- Filter out past events from results

## CSV Schema

Events are logged with the following enhanced structure:

| Column | Description |
|--------|-------------|
| `event_name` | Name of the event |
| `event_date` | Event date (YYYY-MM-DD format) |
| `event_type` | Type/category of event |
| `event_url` | Event website URL |
| `description` | Paragraph summary of the event |
| `ticket_price` | Cost to attend (e.g., "Free", "£25", "Contact for pricing") |
| `venue` | Location/venue name and area |
| `speakers` | Key speakers or notable attendees |
| `date_logged` | When the event was discovered |

## Configuration

Key settings in `config.py`:

- `MODEL_NAME`: OpenAI model to use (default: "gpt-4o")
- `USER_LOCATION`: Search location (default: "London, GB")
- `QUERIES_FILE`: Path to queries file
- `EVENTS_LOG_FILE`: Path to events CSV file

## Deduplication

The system prevents duplicate events using:

1. **Hash-based**: Creates unique hash from event name + date
2. **URL-based**: Checks if the event URL already exists
3. **Automatic**: Runs on every new event before logging

## Error Handling

- Graceful handling of API failures
- JSON parsing error recovery
- Invalid date format handling
- Network timeout management
- Malformed response handling

## Future Enhancements

- 📱 Telegram/email notifications
- ⏰ Scheduled execution (cron/systemd)
- 🌍 Multi-city support
- 🎨 Web dashboard
- 📈 Event trend analysis
- 🔔 Custom alert criteria

## Troubleshooting

**API Key Issues:**
- Ensure your OpenAI API key is valid and has sufficient credits
- Check that the key is properly set in your `.env` file

**No Events Found:**
- Try broader search queries
- Check if the queries in `queries.txt` are relevant and current
- Verify your internet connection

**JSON Parsing Errors:**
- The system automatically handles most parsing issues
- Check the console output for specific error details

## License

This project is open source and available under the MIT License.
