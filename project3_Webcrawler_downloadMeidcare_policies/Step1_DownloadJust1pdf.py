"""
Step1_DownloadJust1pdf.py
Downloads a single Medicare LCD policy as a high-quality PDF using Playwright.

This script downloads the Glucose Monitors LCD (L33822) policy from the CMS Medicare Coverage Database
and saves it as a PDF file while preserving formatting, tables, and all details.
"""

import asyncio
from playwright.async_api import async_playwright
import os
from datetime import datetime

async def download_lcd_policy_as_pdf():
    """
    Downloads a Medicare LCD policy as PDF using Playwright.
    Uses the Glucose Monitors LCD (L33822) as an example.
    """
    
    # LCD URL for Glucose Monitors policy
    lcd_url = "https://www.cms.gov/medicare-coverage-database/view/lcd.aspx?LCDId=33822&DocID=L33822"
    
    # Create output directory if it doesn't exist
    output_dir = "downloaded_policies"
    os.makedirs(output_dir, exist_ok=True)
    
    # Generate filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    pdf_filename = f"{output_dir}/LCD_L33822_Glucose_Monitors_{timestamp}.pdf"
    
    async with async_playwright() as p:
        # Launch browser (use chromium for best PDF rendering)
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        try:
            print(f"Loading LCD policy from: {lcd_url}")
            
            # Navigate to the LCD policy page
            await page.goto(lcd_url, wait_until="networkidle")
            
            # Wait for initial page load
            await page.wait_for_timeout(2000)
            
            # Look for and click "I Accept" button if it exists
            try:
                print("Looking for 'I Accept' button...")
                accept_button = await page.wait_for_selector("input[value='I Accept'], button:has-text('I Accept'), input[type='submit'][value*='Accept']", timeout=5000)
                if accept_button:
                    print("Found 'I Accept' button, clicking...")
                    await accept_button.click()
                    # Wait for page to load after accepting terms
                    await page.wait_for_timeout(3000)
                    print("Terms accepted, page loaded")
                else:
                    print("No 'I Accept' button found, proceeding...")
            except Exception as e:
                print(f"No 'I Accept' button found or error clicking: {e}")
                # Continue anyway in case the button isn't needed
            
            # Wait for content to fully load
            await page.wait_for_timeout(2000)
            
            print("Generating PDF...")
            
            # Generate PDF with high quality settings
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
            
            print(f"✅ PDF successfully saved as: {pdf_filename}")
            print(f"📁 File size: {os.path.getsize(pdf_filename) / (1024*1024):.2f} MB")
            
        except Exception as e:
            print(f"❌ Error downloading LCD policy: {str(e)}")
            raise
            
        finally:
            await browser.close()

async def main():
    """Main function to run the LCD policy download."""
    print("🏥 Medicare LCD Policy Downloader")
    print("=" * 50)
    print("📋 Policy: Glucose Monitors (L33822)")
    print("🌐 Source: CMS Medicare Coverage Database")
    print("=" * 50)
    
    await download_lcd_policy_as_pdf()
    
    print("\n✨ Download completed successfully!")
    print("💡 Tip: Check the 'downloaded_policies' folder for your PDF file.")

if __name__ == "__main__":
    # Install required packages if not already installed
    try:
        import playwright
    except ImportError:
        print("❌ Playwright not found. Please install it first:")
        print("pip install playwright")
        print("playwright install chromium")
        exit(1)
    
    # Run the async main function
    asyncio.run(main())