
import json
import glob
import os
from pathlib import Path
from datetime import datetime

# Import load_all_docs to trigger re-indexing
import load_all_docs

def main():
    print("="*50)
    print("NEWS BRIDGE: Connecting Scraper -> RAG")
    print("="*50)

    # 1. Paths
    # iris-apple-dev (current dir) -> .. -> iris-main -> src -> change_tracking -> new_urls
    scraper_dir = Path(__file__).parent.parent / "iris-main" / "src" / "change_tracking" / "new_urls"
    output_file = Path("documents/scraped_news_summary.txt")

    print(f"Reading news from: {scraper_dir}")
    
    # 2. Get all JSON files
    json_files = list(scraper_dir.glob("*.json"))
    print(f"Found {len(json_files)} scraper data files.")

    # 3. Aggregate News
    aggregated_text = "LATEST FINANCIAL NEWS SUMMARY\n"
    aggregated_text += f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
    aggregated_text += "="*50 + "\n\n"

    total_articles = 0

    for json_file in json_files:
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            company = data.get('company_name', 'Unknown Company')
            new_urls = data.get('new_urls', [])
            
            if not new_urls:
                continue

            aggregated_text += f"--- {company} NEWS ---\n"
            
            for item in new_urls:
                # Extract clean title/text
                text = item.get('text', '').strip()
                url = item.get('url', '')
                date = item.get('discovered_at', '')

                # Filter junk
                if len(text) < 20 or "cookie" in text.lower() or "subscribe" in text.lower():
                    continue
                
                aggregated_text += f"TITLE: {text}\n"
                aggregated_text += f"DATE: {date}\n"
                aggregated_text += f"SOURCE: {url}\n"
                aggregated_text += "-"*20 + "\n"
                total_articles += 1
            
            aggregated_text += "\n"

        except Exception as e:
            print(f"Error reading {json_file.name}: {e}")

    # 4. Write to Documents folder
    output_file.parent.mkdir(exist_ok=True)
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(aggregated_text)

    print(f"Successfully wrote {total_articles} news articles to {output_file}")
    print("\n" + "="*50)
    print("TRIGGERING RAG INDEX UPDATE")
    print("="*50 + "\n")

    # 5. Run standard loader
    load_all_docs.main()

if __name__ == "__main__":
    main()
