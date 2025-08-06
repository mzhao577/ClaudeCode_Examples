"""
Step2_Find_allPolicy_URLs.py
Researches and finds all Medicare LCD (Local Coverage Determination) policy URLs
from the CMS Medicare Coverage Database.

This script will:
1. Navigate to the CMS Medicare Coverage Database search page
2. Search for all LCD policies 
3. Extract all LCD URLs with their policy IDs and titles
4. Save the results to All_urls.json
"""

import asyncio
from playwright.async_api import async_playwright
import json
import re
from datetime import datetime
import time

class LCDPolicyFinder:
    def __init__(self):
        self.base_url = "https://www.cms.gov/medicare-coverage-database/search.aspx"
        self.lcd_urls = []
        self.processed_ids = set()

    async def search_lcd_policies(self, page, search_term="", page_num=1):
        """Search for LCD policies using the CMS search interface."""
        
        try:
            print(f"Searching page {page_num} with term: '{search_term}'")
            
            # Navigate to search page
            await page.goto(self.base_url, wait_until="networkidle")
            await page.wait_for_timeout(2000)
            
            # Handle "I Accept" if it appears
            try:
                accept_button = await page.wait_for_selector("input[value='I Accept'], button:has-text('I Accept')", timeout=3000)
                if accept_button:
                    await accept_button.click()
                    await page.wait_for_timeout(2000)
            except:
                pass
            
            # Select LCD document type
            try:
                lcd_checkbox = await page.wait_for_selector("input[value='LCD']", timeout=5000)
                if lcd_checkbox:
                    await lcd_checkbox.check()
                    print("Selected LCD document type")
            except Exception as e:
                print(f"Could not find LCD checkbox: {e}")
            
            # Enter search term if provided
            if search_term:
                try:
                    search_input = await page.wait_for_selector("input[name*='search'], input[id*='search']", timeout=5000)
                    if search_input:
                        await search_input.fill(search_term)
                except:
                    pass
            
            # Click search button
            try:
                search_button = await page.wait_for_selector("input[type='submit'], button[type='submit']", timeout=5000)
                if search_button:
                    await search_button.click()
                    await page.wait_for_timeout(3000)
                    print("Search submitted")
            except Exception as e:
                print(f"Could not find search button: {e}")
            
            # Extract LCD links from results
            await self.extract_lcd_links(page)
            
        except Exception as e:
            print(f"Error in search: {e}")

    async def extract_lcd_links(self, page):
        """Extract all LCD policy links from the current page."""
        
        try:
            # Wait for results to load
            await page.wait_for_timeout(3000)
            
            # Look for LCD links in various possible formats
            lcd_link_selectors = [
                "a[href*='lcd.aspx']",
                "a[href*='LCDId=']",
                "a[href*='DocID=L']",
                "a:has-text('L')"
            ]
            
            for selector in lcd_link_selectors:
                try:
                    links = await page.query_selector_all(selector)
                    for link in links:
                        href = await link.get_attribute('href')
                        text = await link.inner_text()
                        
                        if href and 'lcd.aspx' in href and 'LCDId=' in href:
                            # Extract LCD ID
                            lcd_id_match = re.search(r'LCDId=(\d+)', href)
                            doc_id_match = re.search(r'DocID=(L\d+)', href)
                            
                            if lcd_id_match and doc_id_match:
                                lcd_id = lcd_id_match.group(1)
                                doc_id = doc_id_match.group(1)
                                
                                if lcd_id not in self.processed_ids:
                                    full_url = href if href.startswith('http') else f"https://www.cms.gov{href}"
                                    
                                    policy_info = {
                                        "lcd_id": lcd_id,
                                        "doc_id": doc_id,
                                        "title": text.strip() if text else f"LCD Policy {doc_id}",
                                        "url": full_url,
                                        "found_date": datetime.now().isoformat()
                                    }
                                    
                                    self.lcd_urls.append(policy_info)
                                    self.processed_ids.add(lcd_id)
                                    print(f"Found LCD {doc_id}: {text.strip()[:50]}...")
                
                except Exception as e:
                    continue
            
            print(f"Total unique LCDs found so far: {len(self.lcd_urls)}")
            
        except Exception as e:
            print(f"Error extracting links: {e}")

    async def extract_all_lcd_results(self, page):
        """Extract all LCD results from search results page with pagination."""
        
        page_num = 1
        max_pages = 50  # Safety limit
        
        while page_num <= max_pages:
            try:
                print(f"Processing results page {page_num}...")
                
                # Wait for results to load
                await page.wait_for_timeout(3000)
                
                # Extract LCD links from current page
                initial_count = len(self.lcd_urls)
                
                # Look for result links in table or list format
                result_selectors = [
                    "a[href*='lcd.aspx?LCDId=']",
                    "table a[href*='LCDId=']",
                    ".searchResults a[href*='lcd.aspx']",
                    "tr a[href*='LCDId=']"
                ]
                
                for selector in result_selectors:
                    try:
                        links = await page.query_selector_all(selector)
                        for link in links:
                            href = await link.get_attribute('href')
                            text = await link.inner_text()
                            
                            if href and 'lcd.aspx' in href and 'LCDId=' in href:
                                # Extract LCD ID and Doc ID
                                lcd_id_match = re.search(r'LCDId=(\d+)', href)
                                doc_id_match = re.search(r'DocID=(L\d+)', href) or re.search(r'(L\d+)', text)
                                
                                if lcd_id_match:
                                    lcd_id = lcd_id_match.group(1)
                                    doc_id = doc_id_match.group(1) if doc_id_match else f"L{lcd_id}"
                                    
                                    if lcd_id not in self.processed_ids:
                                        full_url = href if href.startswith('http') else f"https://www.cms.gov{href}"
                                        
                                        policy_info = {
                                            "lcd_id": lcd_id,
                                            "doc_id": doc_id,
                                            "title": text.strip() if text else f"LCD Policy {doc_id}",
                                            "url": full_url,
                                            "found_date": datetime.now().isoformat()
                                        }
                                        
                                        self.lcd_urls.append(policy_info)
                                        self.processed_ids.add(lcd_id)
                    except:
                        continue
                
                new_count = len(self.lcd_urls) - initial_count
                print(f"Found {new_count} new LCD policies on page {page_num}")
                
                # Look for next page link
                try:
                    next_link = await page.query_selector("a:has-text('Next'), a:has-text('>'), a[title*='Next']")
                    if next_link and new_count > 0:
                        await next_link.click()
                        await page.wait_for_timeout(3000)
                        page_num += 1
                    else:
                        print("No more pages or no new results found")
                        break
                except:
                    print("No next page found")
                    break
                    
            except Exception as e:
                print(f"Error on page {page_num}: {e}")
                break
        
        print(f"Completed pagination. Total LCDs found: {len(self.lcd_urls)}")

    async def comprehensive_search(self):
        """Perform comprehensive search for all LCD policies."""
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            try:
                print("🔍 Starting LCD policy search...")
                
                # Try multiple approaches to find LCD policies
                await self.search_via_reports(page)
                await self.search_via_keyword(page)
                await self.try_known_lcd_patterns(page)
                
            except Exception as e:
                print(f"Error in comprehensive search: {e}")
            finally:
                await browser.close()

    async def search_via_reports(self, page):
        """Search using LCD report pages."""
        
        report_urls = [
            "https://www.cms.gov/medicare-coverage-database/reports/finallcdalphabeticalreport.aspx",
            "https://www.cms.gov/medicare-coverage-database/reports/finallcdcontractorreport.aspx",
            "https://www.cms.gov/medicare-coverage-database/reports/finallcdstatereport.aspx"
        ]
        
        for url in report_urls:
            try:
                print(f"Checking LCD report: {url}")
                await page.goto(url, wait_until="networkidle")
                await page.wait_for_timeout(2000)
                
                # Handle "I Accept" if needed
                try:
                    accept_button = await page.wait_for_selector("input[value='I Accept']", timeout=2000)
                    if accept_button:
                        await accept_button.click()
                        await page.wait_for_timeout(2000)
                except:
                    pass
                
                # Extract LCD links from report page
                await self.extract_lcd_links(page)
                
            except Exception as e:
                print(f"Error with report URL {url}: {e}")

    async def search_via_keyword(self, page):
        """Search using keyword search."""
        
        try:
            await page.goto(self.base_url, wait_until="networkidle")
            await page.wait_for_timeout(2000)
            
            # Handle "I Accept" if needed
            try:
                accept_button = await page.wait_for_selector("input[value='I Accept']", timeout=2000)
                if accept_button:
                    await accept_button.click()
                    await page.wait_for_timeout(2000)
            except:
                pass
            
            # Try to search with LCD keyword
            search_input = await page.query_selector("input[type='text']")
            if search_input:
                await search_input.fill("LCD")
                
                search_button = await page.query_selector("input[type='submit'], button[type='submit']")
                if search_button:
                    await search_button.click()
                    await page.wait_for_timeout(3000)
                    await self.extract_lcd_links(page)
            
        except Exception as e:
            print(f"Error in keyword search: {e}")

    async def try_known_lcd_patterns(self, page):
        """Try to find LCDs using known URL patterns."""
        
        # Generate some known LCD IDs to test the pattern
        test_lcd_ids = range(30000, 40000, 100)  # Sample range
        
        found_count = 0
        for lcd_id in test_lcd_ids:
            if found_count >= 10:  # Limit test to avoid too many requests
                break
                
            try:
                test_url = f"https://www.cms.gov/medicare-coverage-database/view/lcd.aspx?LCDId={lcd_id}"
                await page.goto(test_url, wait_until="networkidle")
                await page.wait_for_timeout(1000)
                
                # Check if this is a valid LCD page
                title = await page.title()
                if "LCD" in title and "Error" not in title:
                    # Extract LCD information
                    try:
                        content = await page.content()
                        if "Local Coverage Determination" in content:
                            policy_info = {
                                "lcd_id": str(lcd_id),
                                "doc_id": f"L{lcd_id}",
                                "title": title,
                                "url": test_url,
                                "found_date": datetime.now().isoformat()
                            }
                            
                            if str(lcd_id) not in self.processed_ids:
                                self.lcd_urls.append(policy_info)
                                self.processed_ids.add(str(lcd_id))
                                found_count += 1
                                print(f"Found valid LCD: L{lcd_id}")
                    except:
                        pass
                        
            except Exception as e:
                continue
        
        print(f"Found {found_count} LCDs via pattern testing")

    async def try_direct_lcd_listings(self, page):
        """Try to find direct LCD listing pages."""
        
        direct_urls = [
            "https://www.cms.gov/medicare-coverage-database/search.aspx?DocType=LCD",
            "https://www.cms.gov/medicare-coverage-database/indexes/lcd-index.html"
        ]
        
        for url in direct_urls:
            try:
                print(f"Trying direct URL: {url}")
                await page.goto(url, wait_until="networkidle")
                await page.wait_for_timeout(3000)
                
                # Handle "I Accept" if needed
                try:
                    accept_button = await page.wait_for_selector("input[value='I Accept']", timeout=2000)
                    if accept_button:
                        await accept_button.click()
                        await page.wait_for_timeout(2000)
                except:
                    pass
                
                await self.extract_lcd_links(page)
                
            except Exception as e:
                print(f"Error with direct URL {url}: {e}")
                continue

    def save_to_json(self, filename="All_urls.json"):
        """Save all found LCD URLs to JSON file."""
        
        # Remove duplicates and sort by LCD ID
        unique_lcds = []
        seen_ids = set()
        
        for lcd in self.lcd_urls:
            if lcd['lcd_id'] not in seen_ids:
                unique_lcds.append(lcd)
                seen_ids.add(lcd['lcd_id'])
        
        # Sort by LCD ID number
        unique_lcds.sort(key=lambda x: int(x['lcd_id']))
        
        # Prepare final data structure
        output_data = {
            "search_date": datetime.now().isoformat(),
            "total_policies": len(unique_lcds),
            "source": "CMS Medicare Coverage Database",
            "policies": unique_lcds
        }
        
        # Save to JSON file
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Saved {len(unique_lcds)} unique LCD policies to {filename}")
        return len(unique_lcds)

async def main():
    """Main function to find all LCD policy URLs."""
    print("🏥 Medicare LCD Policy URL Finder")
    print("=" * 50)
    print("🎯 Target: All Medicare LCD Medical Policies")
    print("🌐 Source: CMS Medicare Coverage Database")
    print("=" * 50)
    
    finder = LCDPolicyFinder()
    
    # Perform comprehensive search
    await finder.comprehensive_search()
    
    # Save results
    total_found = finder.save_to_json("All_urls.json")
    
    print("\n" + "=" * 50)
    print("📊 SEARCH RESULTS")
    print("=" * 50)
    print(f"✅ Total LCD policies found: {total_found}")
    print(f"📁 Results saved to: All_urls.json")
    print("💡 Each URL includes policy ID, title, and direct link")
    
    if total_found > 0:
        print(f"\n📋 Sample policies found:")
        for i, policy in enumerate(finder.lcd_urls[:5]):
            print(f"  {i+1}. {policy['doc_id']}: {policy['title'][:60]}...")
    
    print(f"\n🎉 Search completed successfully!")

if __name__ == "__main__":
    try:
        import playwright
    except ImportError:
        print("❌ Playwright not found. Please install it first:")
        print("pip install playwright")
        print("playwright install chromium")
        exit(1)
    
    asyncio.run(main())