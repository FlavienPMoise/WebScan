#!/usr/bin/env python3
"""
Website Update Monitor - Monitors websites for changes and uses AI to summarize them.

This program:
1. Stores a list of websites to monitor
2. On first run, downloads and stores initial content
3. On subsequent runs, compares current content with stored content
4. Uses Groq API with open-source LLMs to summarize changes
5. Outputs bullet-point summaries of changes

Usage: python website_monitor.py
"""

import os
import sys
import json
import pickle
import argparse
import hashlib
import time
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple

import requests
from bs4 import BeautifulSoup, Comment
from groq import Groq

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class WebsiteMonitor:

    def __init__(self, groq_api_key: str, data_dir: str = "website_data"):
        """
        Initialize the website monitor.

        Args:
            groq_api_key: API key for Groq service
            data_dir: Directory to store website data
        """
        self.groq_client = Groq(api_key=groq_api_key)
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        self.storage_file = self.data_dir / "website_storage.json"

        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36'
        }

        self.model = "llama3-8b-8192"  #cheap and fast model, good enough for our use case

    def get_website_content(self, url: str) -> Tuple[str, str]:
        """
        Fetch and extract text content from a website.

        Args:
            url: Website URL to fetch

        Returns:
            Tuple of (text_content, page_title)
        """
        try:
            logger.info(f"Fetching content from {url}")
            response = requests.get(url, headers=self.headers, timeout=30)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')

            for script in soup(["script", "style", "nav", "footer", "header", "aside"]):
                script.decompose()

            for comment in soup.findAll(text=lambda text: isinstance(text, Comment)):
                comment.extract()

            title_tag = soup.find('title')
            page_title = title_tag.get_text().strip() if title_tag else "No title"

            content_selectors = [
                'article', 'main', '[role="main"]', 
                '.content', '.post', '.entry', '.article',
                '.main-content', '.page-content', '.post-content'
            ]

            main_content = None
            for selector in content_selectors:
                main_content = soup.select_one(selector)
                if main_content:
                    break

            if not main_content:
                main_content = soup.find('body') or soup

            text_content = main_content.get_text(separator=' ', strip=True)

            import re
            text_content = re.sub(r'\s+', ' ', text_content).strip()

            logger.info(f"Successfully extracted {len(text_content)} characters from {url}")
            return text_content, page_title

        except requests.RequestException as e:
            logger.error(f"Failed to fetch {url}: {e}")
            return "", f"Error fetching: {str(e)}"
        except Exception as e:
            logger.error(f"Error processing {url}: {e}")
            return "", f"Error processing: {str(e)}"

    def calculate_content_hash(self, content: str) -> str:
        """Calculate MD5 hash of content for comparison."""
        return hashlib.md5(content.encode('utf-8')).hexdigest()

    def load_stored_data(self) -> Dict:
        """Load previously stored website data."""
        if self.storage_file.exists():
            try:
                with open(self.storage_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                logger.warning(f"Failed to load stored data: {e}")
                return {}
        return {}

    def save_stored_data(self, data: Dict):
        """Save website data to storage."""
        try:
            with open(self.storage_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            logger.info(f"Saved data for {len(data)} websites")
        except IOError as e:
            logger.error(f"Failed to save data: {e}")

    def compare_with_ai(self, url: str, old_content: str, new_content: str, 
                       site_title: str) -> str:
        """
        Use Groq AI to compare website contents and summarize changes.

        Args:
            url: Website URL
            old_content: Previous content
            new_content: Current content
            site_title: Website title

        Returns:
            Summary of changes
        """
        try:
            max_chars = 8000  # Leave room for prompt
            old_truncated = old_content[:max_chars] + "..." if len(old_content) > max_chars else old_content
            new_truncated = new_content[:max_chars] + "..." if len(new_content) > max_chars else new_content

            prompt = f"""
You are analyzing changes between two versions of a website. 
Website: {site_title} ({url})

Please compare the old and new content and provide a concise summary of changes in this exact format:
- [Website Name]: [Brief description of changes]

If there are no meaningful changes, respond with:
- [Website Name]: No significant updates detected.

Focus on:
1. New articles, posts, or content sections
2. Updated information or announcements  
3. New features or functionality
4. Removed content (if significant)

Ignore minor formatting changes, timestamps, or navigation updates.

OLD CONTENT:
{old_truncated}

NEW CONTENT:
{new_truncated}
"""

            chat_completion = self.groq_client.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": "You are a helpful assistant that analyzes website changes and provides concise summaries. Always respond with a single bullet point starting with the website name."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                model=self.model,
                temperature=0.1,  #low temperature for consistent output
                max_tokens=200   # keep responses concise
            )

            response = chat_completion.choices[0].message.content.strip()

            # Ensure the response starts with a bullet point
            if not response.startswith('-'):
                response = f"- {response}"

            return response

        except Exception as e:
            logger.error(f"AI comparison failed for {url}: {e}")
            return f"- {site_title}: Error analyzing changes - {str(e)}"

    def monitor_websites(self, websites: List[str]) -> List[str]:
        """
        Monitor a list of websites for changes.

        Args:
            websites: List of website URLs to monitor

        Returns:
            List of change summaries
        """
        stored_data = self.load_stored_data()
        results = []

        for url in websites:
            logger.info(f"\nProcessing: {url}")

            current_content, site_title = self.get_website_content(url)

            if not current_content:
                results.append(f"- {url}: Failed to fetch content")
                continue

            current_hash = self.calculate_content_hash(current_content)

            if url not in stored_data:
                stored_data[url] = {
                    'content': current_content,
                    'hash': current_hash,
                    'title': site_title,
                    'last_updated': datetime.now().isoformat(),
                    'first_seen': datetime.now().isoformat()
                }
                results.append(f"- {site_title}: Added to monitoring (baseline established)")
                logger.info(f"Baseline established for {url}")

            else:
                stored_hash = stored_data[url].get('hash')
                stored_content = stored_data[url].get('content', '')

                if current_hash == stored_hash:
                    results.append(f"- {site_title}: No updates detected")
                    logger.info(f"No changes detected for {url}")
                else:
                    logger.info(f"Changes detected for {url}, analyzing with AI...")
                    change_summary = self.compare_with_ai(
                        url, stored_content, current_content, site_title
                    )
                    results.append(change_summary)

                    stored_data[url].update({
                        'content': current_content,
                        'hash': current_hash,
                        'title': site_title,
                        'last_updated': datetime.now().isoformat()
                    })

            time.sleep(1)

        self.save_stored_data(stored_data)

        return results


def main():
    parser = argparse.ArgumentParser(
        description='Monitor websites for changes using AI analysis',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python website_monitor.py
  python website_monitor.py --data-dir ./monitoring_data

Environment Variables:
  GROQ_API_KEY: Your Groq API key (required)
        """
    )

    parser.add_argument(
        '--data-dir', 
        default='website_data',
        help='Directory to store monitoring data (default: website_data)'
    )

    parser.add_argument(
        '--model',
        default='llama3-8b-8192',
        choices=['llama3-8b-8192', 'llama3-70b-8192', 'mixtral-8x7b-32768', 'gemma-7b-it'],
        help='LLM model to use for analysis (default: llama3-8b-8192)'
    )

    args = parser.parse_args()

    groq_api_key = os.getenv('GROQ_API_KEY')
    if not groq_api_key:
        print("Error: GROQ_API_KEY environment variable not set")
        print("Get your API key from: https://console.groq.com/")
        print("Then set it with: export GROQ_API_KEY=your_api_key_here")
        sys.exit(1)

    # Website list - USER SHOULD MODIFY THIS ARRAY
    websites = [
        "https://qiyanjun.github.io/2025Fall-UVA-CS-MachineLearningDeep/",
        "https://www.cs.virginia.edu/~up3f/cs4750/",
        "https://yumeng5.github.io/teaching/2025-fall-cs4770"
    ]

    if not websites:
        print("No websites configured for monitoring.")
        print("Please edit the 'websites' list in the script to add URLs to monitor.")
        sys.exit(1)

    monitor = WebsiteMonitor(groq_api_key, args.data_dir)
    monitor.model = args.model

    print(f"Website Update Monitor")
    print(f"Monitoring {len(websites)} website(s)...")
    print(f"Using model: {args.model}")
    print(f"Data directory: {args.data_dir}")
    print("-" * 50)

    try:
        results = monitor.monitor_websites(websites)

        print("\nMonitoring Results:")
        for result in results:
            print(result)

    except KeyboardInterrupt:
        print("\nMonitoring interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Monitoring failed: {e}")
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
