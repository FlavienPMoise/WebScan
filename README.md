# Website Update Monitor

A Python program that monitors websites for changes and uses AI (via Groq API) to intelligently summarize what has been updated. Perfect for tracking professor's websites, webcomics, job boards, or any content that updates regularly.

## Requirements

- Python 3.7+
- Groq API key (free tier is sufficient)
- Internet connection

## Installation

### Quick Setup

1. **Clone or download the files**:
   - `website_monitor.py` - Main program
   - `requirements.txt` - Python dependencies  
   - `setup.sh` - Setup script

2. **Run the setup script**:
   ```bash
   chmod +x setup.sh
   ./setup.sh
   ```

3. **Get your Groq API key**:
   - Visit: https://console.groq.com/
   - Create an account and generate an API key
   - Set the environment variable:
     ```bash
     export GROQ_API_KEY=your_api_key_here
     ```

### Manual Setup (if the setup script doesn't work)

1. **Create virtual environment**:
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # I used linux... for Windows, do: venv\Scripts\activate
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

## Configuration

### Adding Websites to Monitor

Edit the `websites` list in `website_monitor.py`:

```python
websites = [
    "https://news.ycombinator.com",
    "https://www.python.org/jobs/",
    "https://github.com/trending",
    # Add more URLs here
]
```

### Available LLM Models

The program supports several open-source models via Groq:

- `llama3-8b-8192` - Fast, efficient (default)
- `llama3-70b-8192` - More powerful, slower
- `mixtral-8x7b-32768` - Good balance of speed/quality
- `gemma-7b-it` - Google's model

## Usage

### Basic Usage

```bash
# First run - establishes baseline for all websites
python website_monitor.py

# Subsequent runs - detects and reports changes
python website_monitor.py
```

### Advanced Usage

```bash
# Use a different model
python website_monitor.py --model llama3-70b-8192

# Store data in custom directory
python website_monitor.py --data-dir ./my_monitoring_data

# See all options
python website_monitor.py --help
```

### Example Output

```
Website Update Monitor
Monitoring 3 website(s)...
Using model: llama3-8b-8192
Data directory: website_data
--------------------------------------------------

Monitoring Results:
- Hacker News: No updates detected
- Python Job Board: 3 new job postings for Python developers added
```

## How It Works

### First Run
1. **Baseline Establishment**: Visits each website in your list
2. **Content Extraction**: Downloads and extracts main text content using BeautifulSoup
3. **Storage**: Saves content and metadata to local JSON file
4. **Output**: Reports that baseline has been established for each site

### Subsequent Runs
1. **Content Fetching**: Downloads current version of each website
2. **Change Detection**: Compares MD5 hash of current content vs. stored content
3. **AI Analysis**: For changed sites, sends old and new content to Groq LLM for analysis
4. **Summary Generation**: AI generates concise bullet-point summary of changes
5. **Update Storage**: Saves new content for future comparisons

## File Structure

```
├── website_monitor.py      # Main program
├── requirements.txt        # Python dependencies
├── setup.sh               # Setup script
├── website_data/          # Storage directory (created automatically)
│   └── website_storage.json  # Website content and metadata
└── venv/                  # Virtual environment (created by setup)
```

## Troubleshooting

### Common Issues

**"GROQ_API_KEY environment variable not set"**
- Get API key from https://console.groq.com/
- Set it: `export GROQ_API_KEY=your_key_here`
- For permanent setup, add to your `.bashrc` or `.zshrc`

**"Failed to fetch content"**
- Check internet connection
- Some sites may block automated requests
- Try adding different user agents or request delays

**"AI comparison failed"**
- Check Groq API key is valid
- Verify you have API quota remaining
- Content might be too large (automatically truncated)

**No changes detected when you expect them**
- Site might use dynamic content loading (JavaScript)
- Check if the meaningful content is in the extracted text
- Consider monitoring a more specific URL


## API Costs

Groq offers generous free tiers:
- Free tier includes significant monthly quota (1,000 requests per day)
- Cost-effective pricing for additional usage
- Open-source models (Llama 3, Mixtral, Gemma)
- Much faster than traditional APIs

## Best Practices

1. **Start Small**: Begin with 1-2 websites to test
2. **Respectful Monitoring**: Don't check too frequently (avoid being blocked). I run this script at most twice per day. 
3. **Specific URLs**: Monitor specific pages rather than homepages for better results
4. **API Key Security**: Keep your API key private and secure
5. **Regular Cleanup**: Periodically review and clean up stored data
