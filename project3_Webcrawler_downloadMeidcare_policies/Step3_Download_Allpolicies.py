"""
Step3_Download_Allpolicies.py
Downloads multiple Medicare LCD policies as PDF files from the URLs stored in All_urls.json.

Features:
- Option to download all policies or just a sample of 10 (default: 10 for resource conservation)
- Uses the same high-quality PDF generation approach as Step1_DownloadJust1pdf.py
- Stores PDFs in Download_PDFs folder with policy number naming (e.g., Policy_33822.pdf)
- Handles "I Accept" terms automatically
- Progress tracking and error handling
"""

import asyncio
from playwright.async_api import async_playwright
import json
import os
from datetime import datetime
import argparse

class BulkLCDDownloader:
    def __init__(self, sample_only=True, sample_size=10):
        self.sample_only = sample_only
        self.sample_size = sample_size
        self.output_dir = "Download_PDFs"
        self.downloaded_count = 0
        self.failed_count = 0
        self.failed_policies = []
        
        # Create output directory
        os.makedirs(self.output_dir, exist_ok=True)
    
    def load_policy_urls(self):
        """Load policy URLs from All_urls.json."""
        try:
            with open("All_urls.json", 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            policies = data.get('policies', [])
            
            if self.sample_only:
                # Prioritize validated policies for sample
                validated_policies = [p for p in policies if p.get('status') != 'estimated']
                estimated_policies = [p for p in policies if p.get('status') == 'estimated']
                
                # Take validated first, then fill with estimated if needed
                sample_policies = validated_policies[:self.sample_size]
                if len(sample_policies) < self.sample_size:
                    remaining = self.sample_size - len(sample_policies)
                    sample_policies.extend(estimated_policies[:remaining])
                
                policies = sample_policies
            
            print(f"📋 Loaded {len(policies)} policies for download")
            return policies
            
        except FileNotFoundError:
            print("❌ All_urls.json not found. Please run Step2 first.")
            return []
        except json.JSONDecodeError:
            print("❌ Invalid JSON format in All_urls.json")
            return []
    
    async def download_policy_pdf(self, page, policy):
        """Download a single LCD policy as PDF."""
        
        try:
            lcd_id = policy['lcd_id']
            doc_id = policy['doc_id']
            title = policy['title']
            url = policy['url']
            
            # Generate filename using policy number
            pdf_filename = f"{self.output_dir}/Policy_{lcd_id}.pdf"
            
            # Skip if already exists
            if os.path.exists(pdf_filename):
                print(f"⏭️  Skipping {doc_id}: Already exists")
                return True
            
            print(f"🔄 Downloading {doc_id}: {title[:40]}...")
            
            # Navigate to the LCD policy page
            await page.goto(url, wait_until="networkidle", timeout=15000)
            
            # Wait for initial page load
            await page.wait_for_timeout(2000)
            
            # Look for and click "I Accept" button if it exists
            try:
                accept_button = await page.wait_for_selector(
                    "input[value='I Accept'], button:has-text('I Accept'), input[type='submit'][value*='Accept']", 
                    timeout=3000
                )
                if accept_button:
                    await accept_button.click()
                    # Wait for page to load after accepting terms
                    await page.wait_for_timeout(3000)
            except:
                # Continue if no accept button found
                pass
            
            # Wait for content to fully load
            await page.wait_for_timeout(2000)
            
            # Generate PDF with high quality settings (same as Step1)
            await page.pdf(
                path=pdf_filename,
                format='A4',
                margin={
                    'top': '0.5in',
                    'right': '0.5in',
                    'bottom': '0.5in',
                    'left': '0.5in'
                },
                print_background=True,  # Include background colors and images
                display_header_footer=True,
                header_template='<div style="font-size:10px; text-align:center; width:100%;">Medicare LCD Policy - Downloaded from CMS.gov</div>',
                footer_template='<div style="font-size:10px; text-align:center; width:100%;"><span class="pageNumber"></span> of <span class="totalPages"></span></div>',
                prefer_css_page_size=True,
                scale=1.0
            )
            
            # Check if PDF was created successfully
            if os.path.exists(pdf_filename):
                file_size = os.path.getsize(pdf_filename) / (1024*1024)  # MB
                print(f"✅ {doc_id}: Downloaded successfully ({file_size:.2f} MB)")
                self.downloaded_count += 1
                return True
            else:
                print(f"❌ {doc_id}: PDF file not created")
                self.failed_count += 1
                self.failed_policies.append({**policy, 'error': 'PDF not created'})
                return False
                
        except Exception as e:
            print(f"❌ {policy.get('doc_id', 'Unknown')}: Error - {str(e)}")
            self.failed_count += 1
            self.failed_policies.append({**policy, 'error': str(e)})
            return False
    
    async def download_all_policies(self):
        """Download all LCD policies as PDFs."""
        
        # Load policies
        policies = self.load_policy_urls()
        if not policies:
            return
        
        async with async_playwright() as p:
            # Launch browser
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            try:
                print(f"🚀 Starting bulk download of {len(policies)} LCD policies...")
                print(f"📁 Output directory: {self.output_dir}")
                print("=" * 70)
                
                start_time = datetime.now()
                
                # Download each policy
                for i, policy in enumerate(policies, 1):
                    print(f"[{i}/{len(policies)}] ", end="")
                    await self.download_policy_pdf(page, policy)
                    
                    # Small delay between downloads to be respectful
                    await page.wait_for_timeout(1000)
                
                end_time = datetime.now()
                duration = (end_time - start_time).total_seconds()
                
                # Print summary
                self.print_summary(len(policies), duration)
                
            except Exception as e:
                print(f"❌ Error in bulk download: {e}")
            finally:
                await browser.close()
    
    def print_summary(self, total_policies, duration):
        """Print download summary."""
        
        print("\n" + "=" * 70)
        print("📊 DOWNLOAD SUMMARY")
        print("=" * 70)
        print(f"✅ Successfully downloaded: {self.downloaded_count}")
        print(f"❌ Failed downloads: {self.failed_count}")
        print(f"📁 Total files in output folder: {len(os.listdir(self.output_dir))}")
        print(f"⏱️  Total time: {duration:.1f} seconds")
        print(f"📍 Output folder: {os.path.abspath(self.output_dir)}")
        
        if self.failed_policies:
            print(f"\n❌ Failed policies:")
            for policy in self.failed_policies[:5]:
                print(f"   - {policy['doc_id']}: {policy.get('error', 'Unknown error')}")
            if len(self.failed_policies) > 5:
                print(f"   ... and {len(self.failed_policies) - 5} more")
        
        print(f"\n🎉 Bulk download completed!")

def main():
    """Main function with command line argument support."""
    
    parser = argparse.ArgumentParser(description='Download Medicare LCD policies as PDFs')
    parser.add_argument('--all', action='store_true', 
                       help='Download all policies (default: download 10 sample policies)')
    parser.add_argument('--sample-size', type=int, default=10,
                       help='Number of sample policies to download (default: 10)')
    
    args = parser.parse_args()
    
    # Print header
    print("🏥 Medicare LCD Bulk PDF Downloader")
    print("=" * 70)
    
    if args.all:
        print("🎯 Mode: Download ALL policies")
        downloader = BulkLCDDownloader(sample_only=False)
    else:
        print(f"🎯 Mode: Download {args.sample_size} sample policies (default)")
        print("💡 Use --all flag to download all policies")
        downloader = BulkLCDDownloader(sample_only=True, sample_size=args.sample_size)
    
    print("🌐 Source: All_urls.json")
    print("📁 Output: Download_PDFs folder")
    print("=" * 70)
    
    # Run the download
    asyncio.run(downloader.download_all_policies())

if __name__ == "__main__":
    try:
        import playwright
    except ImportError:
        print("❌ Playwright not found. Please install it first:")
        print("pip install playwright")
        print("playwright install chromium")
        exit(1)
    
    main()