from datetime import datetime
from typing import Dict, Set, Tuple
from utils import validate_json
from lxml import html
import os
import httpx, contextlib, json
import asyncio



class ArxivScraper:
    def __init__(self, history_file: str, pages: int, selector_file: str) -> None:
        self.history_file = history_file
        self.history = self.read_history_file(history_file)
        self.selectors = self.read_selector_file(selector_file)
        self.pages = pages
        self.session = httpx.AsyncClient()        

    def read_history_file(self, filename: str) -> Set[str]:
        with contextlib.suppress(FileNotFoundError):
            with open(filename, "rt") as fp:
                return {line.strip() for line in fp.readlines()}
        return set()

    def write_history_file(self, history: Set[str]) -> None:
        history = [f"{line}\n" for line in history]
        with open(self.history_file, "wt") as fp:
            fp.writelines(history)

    def read_selector_file(self, filename: str) -> Dict[str, str]:
        selector_schema = {
            "type": "object",
            "properties": {
                "baseUrl": {"type": "string"},
            },
        }

        try:
            with open(filename, "r") as fp:
                json_data = json.load(fp)
            if validate_json(json_data, selector_schema):
                return json_data
            else:
                raise TypeError("Schema not Valid")
        except Exception as e:
            print(f"Error reading the selector file. Details {e}")

    async def download_pdf_async(
        self, link: str, filename: str, semaphore: asyncio.Semaphore
    ) -> None:
        async with semaphore:
            response = await self.session.get(link)
            with open(filename, "wb") as f:
                f.write(response.content)

    async def start(self, max_concurrency=5, days_limit=2, pdf_limit=10) -> list[dict[str, str]]:
        if not os.path.exists("pdfs"):
            os.makedirs("pdfs")
                    
        self.history = self.read_history_file(self.history_file)

        link_dict, title_dict = await self.scrape_page(self.selectors["baseUrl"])
        
        filtered_dict = self.get_closest_items(link_dict, days_limit)
        
        all_links = set()
        all_files = []
        
        pdfs_downloaded_count = 0
        stop_processing = False

        for date, links in filtered_dict.items():
            to_get = links.difference(self.history)
            tasks = []
            semaphore = asyncio.Semaphore(max_concurrency)
            
            for link in to_get:
                if stop_processing:
                    break # break out of the outer loop
                
                print(f"Queuing {link} for download")
                title = title_dict[link]
                filename = f"{link.split('/')[-1][:-4]}__{self.string_to_date_string(date)}__{title}.pdf"
                filepath = os.path.join("pdfs", filename)
                
                all_files.append({"file_path" : filepath, "title" : title, "link" : link})
                
                task = asyncio.create_task(
                    self.download_pdf_async(
                        link,
                        filepath,
                        semaphore,
                    )
                )
                pdfs_downloaded_count += 1 
                if pdfs_downloaded_count >= pdf_limit:
                    stop_processing = True 
                    break 
                
                tasks.append(task)

            all_links.update(links)
            
            if stop_processing:
                break 

        await asyncio.gather(*tasks)
        links = self.history.union(all_links)
        self.write_history_file(links)

        return all_files


    def string_to_date_string(self, string: str) -> str:
        date_obj = datetime.strptime(string, "%a, %d %b %Y")
        return date_obj.strftime("%-d-%-m-%y")
    
    def get_closest_items(self, items_dict: dict, number_items: int):
        target_date = datetime.now()
        sorted_items = sorted(items_dict.items(), key=lambda x: abs(target_date - self.string_to_date(x[0])))
        return dict(sorted_items[:number_items])

    def string_to_date(self, string: str) -> datetime:
        return datetime.strptime(string, "%a, %d %b %Y")

    async def scrape_page(self, link: str) -> Tuple[Dict[str, Set[str]], Dict[str, str]]:
        request = await self.session.get(link)
        page = request.content
        tree = html.fromstring(page)
        dates = tree.xpath("//h3")
        links = {}
        
        
        for date in dates:
            research_papers_pdfs = date.xpath(
                "./following-sibling::dl[1][preceding-sibling::h3[1]]//span[@class = 'list-identifier']//a[@title = 'Download PDF']"
            )
            
            links[date.text_content()] = {
                f'https://arxiv.org{paper.get("href")}.pdf'
                for paper in research_papers_pdfs
            }
            
        research_papers_pdfs = tree.xpath(
            "//following-sibling::dl[1][preceding-sibling::h3[1]]//span[@class = 'list-identifier']//a[@title = 'Download PDF']"
        )
        titles = tree.xpath(
            '//following-sibling::dl[1][preceding-sibling::h3[1]]//div[@class = "list-title mathjax"]'
        )

        title_dict = {f'https://arxiv.org{paper.get("href")}.pdf' : title.text_content().replace("Title:", "").strip().replace(" ", "-")[:100] for title, paper in zip(titles, research_papers_pdfs)}

        return links, title_dict


async def main():
    scraper = ArxivScraper("history_file.txt", 2, "selectors.json")
    await scraper.start()


if __name__ == "__main__":
    asyncio.run(main())
