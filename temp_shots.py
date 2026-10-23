"""Temporary: render the live dashboard in headless Chrome and screenshot key states."""
import os
import sys
import time
from selenium import webdriver
from selenium.webdriver.common.by import By

OUT = os.path.join(os.environ["TEMP"], "tashots")
os.makedirs(OUT, exist_ok=True)

opts = webdriver.ChromeOptions()
opts.add_argument("--headless=new")
opts.add_argument("--window-size=1600,1200")
opts.add_argument("--hide-scrollbars")
drv = webdriver.Chrome(options=opts)
drv.get("http://localhost:8765/")
time.sleep(12)


def tab(label_start):
    tabs = drv.find_elements(By.XPATH, f"//*[@role='tab'][contains(., '{label_start}')]")
    if tabs:
        drv.execute_script("arguments[0].click();", tabs[0])
        time.sleep(6)
        return
    print("tab not found", label_start, [t.text for t in drv.find_elements(By.XPATH, "//*[@role='tab']")])


def shot(name):
    drv.save_screenshot(os.path.join(OUT, name + ".png"))
    print("saved", name)


def scroll_to_map():
    els = drv.find_elements(By.CSS_SELECTOR, '[data-testid="stDeckGlJsonChart"]')
    print("deck charts found:", len(els))
    if els:
        drv.execute_script("arguments[0].scrollIntoView({block:'center'});", els[0])
        time.sleep(6)
        canv = els[0].find_elements(By.TAG_NAME, "canvas")
        print("canvases in deck:", len(canv))


# Logo
imgs = drv.find_elements(By.CSS_SELECTOR, '[data-testid="stSidebarLogo"], [data-testid="stLogo"], img[data-testid="stLogo"]')
print("logo elements:", len(imgs), [i.get_attribute("naturalWidth") for i in imgs])
shot("01_home_uk")

tab("WHERE?")
scroll_to_map()
shot("02_map_uk")

# Switch study context
for lab in drv.find_elements(By.CSS_SELECTOR, '[data-testid="stSidebar"] label'):
    if "India Transferability" in lab.text:
        lab.click()
        break
time.sleep(10)
tab("WHERE?")
scroll_to_map()
shot("03_map_india")
tab("UNDER WHAT CONDITIONS")
shot("04_conditions_india")
tab("WHEN?")
shot("05_when_india")
for ex in drv.find_elements(By.CSS_SELECTOR, '[data-testid="stException"]'):
    print("EXCEPTION ON PAGE:", ex.text[:300])

logs = [l for l in drv.get_log("browser")] if hasattr(drv, "get_log") else []
for l in logs[-15:]:
    print("console:", l.get("level"), l.get("message")[:200])
drv.quit()
