# Agent Toolkit

A powerful Python-based toolkit for web search and URL scraping operations, built with FastAPI and modern web technologies.

## Features

- **Web Search API**: Perform web searches with rate limiting and error handling
- **URL Scraping**: Extract content from web pages with optional JavaScript rendering
- **Rate Limiting**: Built-in rate limiting for API endpoints
- **Configuration Management**: Flexible configuration system for different components
- **Modern Stack**: Built with FastAPI, Pydantic, and Playwright

## Prerequisites

- Python 3.8 or higher
- pip (Python package installer)

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd agent_toolkit
```

2. Install the required dependencies:
```bash
pip install -r requirements.txt
```

3. Install Playwright browsers:
```bash
playwright install
```

## Configuration

The project uses a configuration system that can be customized in the `config` directory. Make sure to set up your environment variables in the `.env` file if required.

## Usage

### Starting the Server

Run the server using:
```bash
python -m agent_toolkit
```

The server will start on `http://127.0.0.1:32823`

### API Endpoints

#### Web Search

```http
POST /search_web
Content-Type: application/json

{
    "query": "your search query"
}
```

#### URL Scraping

```http
POST /scrape_url
Content-Type: application/json

{
    "url": "https://example.com",
    "render_js": false
}
```

## Project Structure

```
agent_toolkit/
├── config/         # Configuration files
├── server/         # FastAPI server implementation
├── tools/          # Core functionality tools
├── examples/       # Example usage
└── __main__.py     # Application entry point
```

## Dependencies

- requests >= 2.31.0
- urllib3 >= 2.0.7
- playwright >= 1.41.0
- markdownify >= 0.11.6
- pydantic >= 2.5.0

## Rate Limiting

The API endpoints are protected by rate limiting to ensure fair usage. Rate limits are configurable in the respective configuration files.

## Error Handling

The API provides detailed error messages and appropriate HTTP status codes for various scenarios:
- 400: Bad Request (invalid input)
- 500: Internal Server Error (server-side issues)

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

[Add your license information here]

## Support

[Add support contact information here] 