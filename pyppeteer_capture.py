import asyncio
from pyppeteer import launch
import sys
import os

async def html_to_image_pyppeteer(html_file_path, output_path):
    # Read the HTML content from the file
    with open(html_file_path, 'r', encoding='utf-8') as html_file:
        html_string = html_file.read()

    # Launch Pyppeteer
    browser = await launch(headless=True)
    page = await browser.newPage()

    # Set the content from the HTML string
    await page.setContent(html_string)

    # Wait for the page to fully load dynamic content
    await page.waitForSelector('body')  # Wait for the body tag
    await page.waitFor(1000)  # Wait for 1 second to ensure content is fully loaded

    # Take a screenshot and save it as a PNG
    await page.screenshot({'path': os.path.abspath(output_path), 'fullPage': True})
    await browser.close()

if __name__ == '__main__':
    html_file_path = sys.argv[1]
    output_path = sys.argv[2]

    # Use asyncio.run to execute the async function
    asyncio.run(html_to_image_pyppeteer(html_file_path, output_path))
