import sys
import asyncio
from pyppeteer import launch

async def capture_html_as_image(html_file_path, output_file_name):
    browser = await launch(headless=True)
    page = await browser.newPage()

    # Open the HTML file in the browser
    await page.goto(f'file://{html_file_path}')
    
    # Wait for the content to load (adjust as necessary)
    await page.waitForSelector('body')  

    # Take a screenshot of the page
    await page.screenshot({'path': output_file_name})
    await browser.close()

def main():
    if len(sys.argv) != 3:
        print("Usage: python pyppeteer_capture.py <html_file_path> <output_image_path>")
        sys.exit(1)
    
    html_file_path = sys.argv[1]
    output_image_path = sys.argv[2]

    asyncio.get_event_loop().run_until_complete(capture_html_as_image(html_file_path, output_image_path))

if __name__ == '__main__':
    main()
