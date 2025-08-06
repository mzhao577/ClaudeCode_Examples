"""
Step2_Quick_LCD_Finder.py
Quick and efficient approach to find Medicare LCD policy URLs by testing
known patterns and ranges with minimal requests.
"""

import asyncio
from playwright.async_api import async_playwright
import json
from datetime import datetime

async def quick_find_lcd_policies():
    """Quickly find a representative sample of LCD policies."""
    
    # Known working LCD IDs and likely ranges
    test_ids = [
        # Known working from our research
        33822, 35000, 35070, 33803, 33393, 38617,
        # Systematic sampling in likely ranges
        33000, 33100, 33200, 33300, 33400, 33500, 33600, 33700, 33800, 33900,
        34000, 34100, 34200, 34300, 34400, 34500, 34600, 34700, 34800, 34900,
        35100, 35200, 35300, 35400, 35500, 35600, 35700, 35800, 35900,
        36000, 36100, 36200, 36300, 36400, 36500, 36600, 36700, 36800, 36900,
        37000, 37100, 37200, 37300, 37400, 37500, 37600, 37700, 37800, 37900,
        38000, 38100, 38200, 38300, 38400, 38500, 38600, 38700, 38800, 38900,
        39000, 39100, 39200, 39300, 39400, 39500, 39600, 39700, 39800, 39900
    ]
    
    lcd_policies = []
    found_count = 0
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        print("🏥 Quick Medicare LCD Policy Finder")
        print("=" * 50)
        print(f"🔍 Testing {len(test_ids)} potential LCD IDs...")
        
        try:
            for i, lcd_id in enumerate(test_ids):
                try:
                    url = f"https://www.cms.gov/medicare-coverage-database/view/lcd.aspx?LCDId={lcd_id}"
                    
                    # Quick navigation with short timeout
                    await page.goto(url, wait_until="domcontentloaded", timeout=8000)
                    
                    # Handle "I Accept" quickly
                    try:
                        accept_button = await page.wait_for_selector("input[value='I Accept']", timeout=1500)
                        if accept_button:
                            await accept_button.click()
                            await page.wait_for_timeout(1000)
                    except:
                        pass
                    
                    # Quick validation
                    title = await page.title()
                    
                    if ("LCD" in title and 
                        "Error" not in title and 
                        "Not Found" not in title and
                        "Search" not in title):
                        
                        # Extract title quickly
                        try:
                            h1 = await page.query_selector("h1")
                            if h1:
                                policy_title = await h1.inner_text()
                            else:
                                policy_title = title.replace(" - CMS", "").strip()
                        except:
                            policy_title = f"LCD Policy L{lcd_id}"
                        
                        policy_info = {
                            "lcd_id": str(lcd_id),
                            "doc_id": f"L{lcd_id}",
                            "title": policy_title.strip(),
                            "url": url,
                            "found_date": datetime.now().isoformat()
                        }
                        
                        lcd_policies.append(policy_info)
                        found_count += 1
                        print(f"✅ Found #{found_count}: L{lcd_id} - {policy_title[:40]}...")
                
                except Exception as e:
                    # Skip failed IDs silently
                    pass
                
                # Progress update
                if (i + 1) % 10 == 0:
                    print(f"   Progress: {i+1}/{len(test_ids)} tested, {found_count} found")
            
        except Exception as e:
            print(f"Error: {e}")
        finally:
            await browser.close()
    
    return lcd_policies

def save_lcd_policies(policies, filename="All_urls.json"):
    """Save LCD policies to JSON file."""
    
    # Sort by LCD ID
    policies.sort(key=lambda x: int(x['lcd_id']))
    
    output_data = {
        "search_date": datetime.now().isoformat(),
        "total_policies": len(policies),
        "source": "CMS Medicare Coverage Database",
        "search_method": "Quick ID sampling",
        "policies": policies
    }
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
    
    return len(policies)

async def main():
    """Main function."""
    print("🚀 Starting quick LCD policy discovery...")
    
    # Find LCD policies
    policies = await quick_find_lcd_policies()
    
    # Save results
    total_found = save_lcd_policies(policies)
    
    print("\n" + "=" * 50)
    print("📊 RESULTS SUMMARY")
    print("=" * 50)
    print(f"✅ Total LCD policies found: {total_found}")
    print(f"📁 Results saved to: All_urls.json")
    
    if total_found > 0:
        print("\n📋 Found policies:")
        for i, policy in enumerate(policies[:15]):
            print(f"  {i+1:2d}. {policy['doc_id']}: {policy['title'][:50]}...")
        
        if total_found > 15:
            print(f"       ... and {total_found - 15} more policies")
    
    print(f"\n🎉 Quick discovery completed!")

if __name__ == "__main__":
    asyncio.run(main())