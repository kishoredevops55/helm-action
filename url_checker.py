import httpx
import asyncio

class AdvancedURLChecker:
    def __init__(self, timeout=10, max_retries=3):
        self.timeout = timeout
        self.max_retries = max_retries

    async def fetch(self, client, url):
        """Check if the URL is accessible with status code 200"""
        for retry in range(self.max_retries):
            try:
                response = await client.get(url)
                if response.status_code == 200:
                    return True, response.status_code
                return False, response.status_code
            except (httpx.RequestError, httpx.TimeoutException) as exc:
                print(f"Error: {exc}. Retrying {retry + 1}/{self.max_retries}")
        return False, None

    async def check_urls(self, urls):
        """Check multiple URLs concurrently"""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            tasks = [self.fetch(client, url) for url in urls]
            results = await asyncio.gather(*tasks)
            for url, (is_accessible, status_code) in zip(urls, results):
                if is_accessible:
                    print(f"{url}: Accessible (Status {status_code})")
                else:
                    print(f"{url}: Inaccessible")

# Example usage
async def main():
    urls = [
        "https://www.google.com",
        "https://github.com",
        "https://www.github.com"
    ]
    
    checker = AdvancedURLChecker(timeout=5, max_retries=2)
    await checker.check_urls(urls)

if __name__ == "__main__":
    asyncio.run(main())
