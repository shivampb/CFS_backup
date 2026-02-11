from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from app.core.config import MAX_TIMEOUT

def create_driver():
    """Create and configure a Chrome WebDriver instance"""
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    # WebGL and DevTools configurations
    chrome_options.add_argument("--enable-unsafe-swiftshader")
    chrome_options.add_argument("--disable-software-rasterizer")
    chrome_options.add_argument("--disable-webgl")
    chrome_options.add_argument("--disable-webgl2")
    # Performance optimizations
    chrome_options.add_argument("--disable-javascript-harmony-shipping")
    chrome_options.add_argument("--disable-dev-tools")
    chrome_options.add_argument("--dns-prefetch-disable")
    chrome_options.add_argument("--disable-background-networking")
    chrome_options.page_load_strategy = "eager"
    chrome_options.add_experimental_option("excludeSwitches", ["enable-logging"])
    chrome_options.add_argument("--log-level=3")

    driver = webdriver.Chrome(options=chrome_options)
    driver.set_page_load_timeout(MAX_TIMEOUT)
    driver.set_script_timeout(MAX_TIMEOUT)
    return driver
