import asyncio
from pyppeteer import launch
import sys
import os

async def html_to_image_pyppeteer(html_file_path, output_path):
    with open(html_file_path, 'r', encoding='utf-8') as html_file:
        html_string = html_file.read()

    browser = await launch(headless=True)
    page = await browser.newPage()

    # Set the content from the HTML string
    await page.setContent(html_string)

    await page.waitForSelector('body') 
    await page.waitFor(1000) 

    await page.screenshot({'path': os.path.abspath(output_path), 'fullPage': True})
    await browser.close()

if __name__ == '__main__':
    html_file_path = sys.argv[1]
    output_path = sys.argv[2]

    # Use asyncio.run to execute the async function
    asyncio.run(html_to_image_pyppeteer(html_file_path, output_path))
