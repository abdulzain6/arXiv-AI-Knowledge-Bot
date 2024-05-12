# arXiv AI Knowledge Bot

The arXiv AI Knowledge Bot is a Discord bot designed to automatically scrape arXiv.com for new publications, adding them to an AI-powered knowledge base. This enables the bot to answer complex queries related to the subjects covered in the articles, making it a valuable resource for academic and research communities on Discord.

## Features

- **Automated Scraping**: Periodically scrapes new publications from arXiv.com.
- **Knowledge Base Integration**: Uses Pinecone to manage a growing index of document data.
- **AI-Powered Answers**: Leverages OpenAI to answer questions based on the indexed knowledge.

## Prerequisites

- Python 3.10 or higher
- Discord Bot Token
- Pinecone API Key
- Access to OpenAI API

## Installation

1. **Clone the repository:**

```bash
git clone https://github.com/abdulzain6/arXiv-AI-Knowledge-Bot.git
cd arXiv-AI-Knowledge-Bot
```

2. **Install the required Python packages:**

```bash
pip install -r requirements.txt
```

## Configuration

Fill in the required API credentials in `credentials.py`:

```python
PINECONE_API_KEY = "your_pinecone_api_key"
PINECONE_ENVIRONMENT = "your_pinecone_environment"
INDEX_NAME = "pdf-gpt-index"
OPENAI_API_KEY = "your_openai_api_key"
BOT_TOKEN = "your_discord_bot_token"
```

## Usage

To run the bot:

```bash
python discord_bot.py
```

Once running, the bot will listen for commands on Discord and provide answers based on the knowledge accumulated from arXiv articles.

## Contributing

We welcome contributions from the community. If you have improvements or fixes, please fork this repository, commit your updates, and submit a pull request.