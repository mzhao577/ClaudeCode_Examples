"""
Step2_Find_allPolicy_URLs_Simple.py
A more efficient approach to find Medicare LCD policy URLs by using known patterns
and validating them systematically.
"""

import asyncio
from playwright.async_api import async_playwright
import json
import re
from datetime import datetime

class SimpleLCDFinder:
    def __init__(self):
        self.lcd_urls = []
        self.processed_ids = set()
        
        # Known working LCD IDs from our research
        self.known_working_ids = [33822, 35000, 35070, 33803, 33393, 38617]
        
    async def validate_lcd_url(self, page, lcd_id):
        """Validate if an LCD ID corresponds to a real policy."""
        
        try:
            url = f"https://www.cms.gov/medicare-coverage-database/view/lcd.aspx?LCDId={lcd_id}"
            await page.goto(url, wait_until="networkidle", timeout=10000)
            
            # Handle "I Accept" if needed
            try:
                accept_button = await page.wait_for_selector("input[value='I Accept']", timeout=2000)
                if accept_button:
                    await accept_button.click()
                    await page.wait_for_timeout(1000)
            except:
                pass
            
            # Check if this is a valid LCD page
            try:
                # Look for LCD content indicators
                content = await page.content()
                title = await page.title()
                
                if ("Local Coverage Determination" in content or 
                    "LCD" in title and "Error" not in title and "Not Found" not in title):
                    
                    # Extract policy title
                    try:
                        title_element = await page.query_selector("h1, .title, #title")
                        if title_element:
                            policy_title = await title_element.inner_text()
                        else:
                            policy_title = title.replace(" - CMS", "").strip()
                    except:
                        policy_title = f"LCD Policy L{lcd_id}"
                    
                    # Look for Doc ID in content
                    doc_id_match = re.search(r'(L\d+)', content)
                    doc_id = doc_id_match.group(1) if doc_id_match else f"L{lcd_id}"
                    
                    policy_info = {
                        "lcd_id": str(lcd_id),
                        "doc_id": doc_id,
                        "title": policy_title.strip(),
                        "url": url,
                        "found_date": datetime.now().isoformat()
                    }
                    
                    return policy_info
                    
            except Exception as e:
                pass
                
        except Exception as e:
            pass
        
        return None
    
    async def find_lcd_policies_systematically(self):
        """Find LCD policies by testing ID ranges systematically."""
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            try:
                print("🔍 Starting systematic LCD discovery...")
                
                # First, validate our known working IDs
                print("📋 Validating known LCD policies...")
                for lcd_id in self.known_working_ids:
                    policy = await self.validate_lcd_url(page, lcd_id)
                    if policy and str(lcd_id) not in self.processed_ids:
                        self.lcd_urls.append(policy)
                        self.processed_ids.add(str(lcd_id))
                        print(f"✅ {policy['doc_id']}: {policy['title'][:50]}...")
                
                # Now search systematically in common ranges
                print("\n🔍 Searching for additional LCD policies...")
                
                # Common LCD ID ranges based on observed patterns
                search_ranges = [
                    (33000, 34000, 50),   # Range around known working IDs
                    (35000, 36000, 50),   # Another active range
                    (37000, 39000, 100),  # Newer policies
                    (30000, 33000, 100),  # Older policies
                    (25000, 30000, 200),  # Much older policies
                ]
                
                total_tested = 0
                for start, end, step in search_ranges:
                    print(f"🔍 Testing range {start}-{end} (step {step})...")
                    range_found = 0
                    
                    for lcd_id in range(start, end, step):
                        if str(lcd_id) not in self.processed_ids:
                            policy = await self.validate_lcd_url(page, lcd_id)
                            if policy:
                                self.lcd_urls.append(policy)
                                self.processed_ids.add(str(lcd_id))
                                range_found += 1
                                print(f"✅ Found: {policy['doc_id']} - {policy['title'][:40]}...")
                            
                            total_tested += 1
                            
                            # Progress indicator
                            if total_tested % 20 == 0:
                                print(f"   Tested {total_tested} IDs, found {len(self.lcd_urls)} total policies")
                    
                    print(f"   Range {start}-{end}: Found {range_found} new policies")
                    
                    # If we found many in this range, search more densely
                    if range_found > 5:
                        print(f"   Dense search in productive range {start}-{end}...")
                        for lcd_id in range(start, end, 10):  # Much smaller step
                            if str(lcd_id) not in self.processed_ids:
                                policy = await self.validate_lcd_url(page, lcd_id)
                                if policy:
                                    self.lcd_urls.append(policy)
                                    self.processed_ids.add(str(lcd_id))
                                    print(f"✅ Dense search: {policy['doc_id']} - {policy['title'][:30]}...")
                
                print(f"\n🎉 Systematic search completed!")
                print(f"📊 Total LCD policies discovered: {len(self.lcd_urls)}")
                
            except Exception as e:
                print(f"Error in systematic search: {e}")
            finally:
                await browser.close()
    
    def save_to_json(self, filename="All_urls.json"):
        """Save all found LCD URLs to JSON file."""
        
        # Sort by LCD ID number
        self.lcd_urls.sort(key=lambda x: int(x['lcd_id']))
        
        # Prepare final data structure
        output_data = {
            "search_date": datetime.now().isoformat(),
            "total_policies": len(self.lcd_urls),
            "source": "CMS Medicare Coverage Database",
            "search_method": "Systematic ID validation",
            "policies": self.lcd_urls
        }
        
        # Save to JSON file
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Saved {len(self.lcd_urls)} LCD policies to {filename}")
        return len(self.lcd_urls)

async def main():
    """Main function to find all LCD policy URLs."""
    print("🏥 Simple Medicare LCD Policy URL Finder")
    print("=" * 60)
    print("🎯 Target: All Medicare LCD Medical Policies")
    print("🌐 Source: CMS Medicare Coverage Database")  
    print("🔧 Method: Systematic ID validation")
    print("=" * 60)
    
    finder = SimpleLCDFinder()
    
    # Find LCD policies systematically
    await finder.find_lcd_policies_systematically()
    
    # Save results
    total_found = finder.save_to_json("All_urls.json")
    
    print("\n" + "=" * 60)
    print("📊 FINAL RESULTS")
    print("=" * 60)
    print(f"✅ Total LCD policies found: {total_found}")
    print(f"📁 Results saved to: All_urls.json")
    print("💡 Each entry includes LCD ID, Doc ID, title, and URL")
    
    if total_found > 0:
        print(f"\n📋 Sample policies found:")
        for i, policy in enumerate(finder.lcd_urls[:10]):
            print(f"  {i+1:2d}. {policy['doc_id']:6s}: {policy['title'][:50]}...")
        
        if total_found > 10:
            print(f"       ... and {total_found - 10} more policies")
    
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