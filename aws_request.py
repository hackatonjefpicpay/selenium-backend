from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.keys import Keys
import datetime
import json


def get_AWS_status(region):
    region = region.lower()

    ano_atual = datetime.datetime.now().year

    data = {
        "request_status": {"status": 200, "description": "Ok"},
        "metadata": {
            "region": region.capitalize(),
            "query_time": datetime.datetime.now().isoformat(),
        },
        "services": {},
    }

    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--blink-settings=imagesEnabled=false")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--disable-software-rasterizer")

    driver = webdriver.Chrome(options=chrome_options)
    try:
        driver.get("https://health.aws.amazon.com/health/status")
        WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located(
                (By.CLASS_NAME, "awsui_row_wih1l_1l1xk_301")
            )
        )

        input_element = driver.find_element(
            By.XPATH, '//input[@aria-label="Find an AWS service or Region"]'
        )
        input_element.send_keys(f"Region = {region}")
        input_element.send_keys(Keys.ENTER)

        try:
            link = driver.find_element(
                By.XPATH,
                '//div[@class="awsui_footer-wrapper_wih1l_1l1xk_280 awsui_variant-container_wih1l_1l1xk_161"]/div/span/div/a',
            )
            driver.execute_script("arguments[0].click();", link)
        except NoSuchElementException:
            pass

        tr_header = driver.find_element(By.TAG_NAME, "tr")
        tr_header_data = [
            _.text
            for _ in tr_header.find_elements(By.TAG_NAME, "th")
            if _.text not in ["RSS", "", "Service"]
        ]

        for i in range(len(tr_header_data)):
            try:
                tr_header_data[i] = (
                    datetime.datetime.strptime(
                        f"{tr_header_data[i]} {ano_atual}", "%d %b %Y"
                    )
                ).strftime("%Y-%m-%d")
            except ValueError:
                pass

        for row in driver.find_elements(By.TAG_NAME, "tr")[1:]:
            cells = row.find_elements(By.TAG_NAME, "td")
            if cells:
                row_data = [cells[0].text.strip()]
                for cell in cells[1:]:
                    if cell.find_elements(By.CSS_SELECTOR, "div[role='button']"):
                        div_button = cell.find_element(
                            By.CSS_SELECTOR, "div[role='button']"
                        )
                        if (
                            div_button.get_attribute("aria-label").strip()
                            == "No Reported Event"
                        ):
                            event_info = {
                                "title": None,
                                "status": "No Reported Event",
                                "summary": None,
                                "description": None,
                            }
                        else:
                            driver.execute_script("arguments[0].click();", div_button)
                            event_info = {
                                "title": cell.find_element(
                                    By.CLASS_NAME, "popover-content-layout"
                                )
                                .find_element(By.TAG_NAME, "h2")
                                .text,
                                "status": cell.find_element(
                                    By.CLASS_NAME, "popover-content-layout"
                                )
                                .find_element(By.TAG_NAME, "span")
                                .text,
                                "summary": cell.find_element(
                                    By.CLASS_NAME, "popover-content-layout"
                                )
                                .find_element(By.TAG_NAME, "p")
                                .text,
                                "description": cell.find_element(
                                    By.CLASS_NAME, "popover-content-layout"
                                )
                                .find_element(By.TAG_NAME, "div")
                                .text,
                            }
                        event_info = {
                            k: v for k, v in event_info.items() if v is not None
                        }
                        row_data.append(event_info)
                data["services"][row_data[0]] = dict(zip(tr_header_data, row_data[1:]))

    except Exception as error:
        data["request_status"]["status"] = 404
        data["request_status"]["description"] = "Bad request"
    finally:
        driver.quit()

    return data
