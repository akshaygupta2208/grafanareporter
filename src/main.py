import time
import os
import sys
import json
import datetime
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

# mail
import smtplib
from email import encoders
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email.mime.image import MIMEImage


def screenshot_dashboard(driver, dashboardURL, imageName, report_dash_timeout):

    driver.get(dashboardURL)
    logger("info", f"Loading grafana report dashboard with timeout {report_dash_timeout}: {dashboardURL}")
    time.sleep(report_dash_timeout)
    imageName = imageName + ".png"
    logger("info", f"Taking screenshot : {imageName}")
    screenshot = driver.save_screenshot(imageName)


def mail_report(imageName, report_email_sub, report_dash_url, date):

    SMTP_SERVER = os.environ['SMTP_SERVER']
    strFrom = os.environ['SENDER_EMAIL']
    strTo = os.environ['RECEIVER_EMAIL']

    dryrun = os.environ['DRYRUN']  # override email id for testing
    if dryrun == "True":
        strTo = os.environ['DRYRUN_EMAIL']

    imageName = imageName + ".png"
    smtp_port = 25

    msgRoot = MIMEMultipart('related')
    msgRoot['Subject'] = report_email_sub
    msgRoot['From'] = strFrom
    msgRoot['To'] = strTo
    msgRoot.preamble = 'Multi-part message in MIME format.'

    msgAlternative = MIMEMultipart('alternative')
    msgRoot.attach(msgAlternative)

    msgText = MIMEText('Alternative plain text message.')
    msgAlternative.attach(msgText)

    htmltext = f"""
    <b><h2>{date}: - {report_email_sub}</h2></b><br>
    <div> <img src="cid:{imageName}" width="900" height="600"></div>
    <br>
    <a href={report_dash_url}>Grafana Dashboard URL</a>
    <br />
    """
    log = {
        "from": strFrom,
        "to": strTo,
        "subject": report_email_sub,
        "status": "Sending Email"
    }

    logger("info", f"{log}")

    msgText = MIMEText(htmltext, 'html')
    msgAlternative.attach(msgText)

    # Attach Image
    fp = open(imageName, 'rb')  # Read image
    msgImage = MIMEImage(fp.read())
    fp.close()

    # Define the image's ID as referenced above
    msgImage.add_header('Content-ID', f"<{imageName}>")
    msgRoot.attach(msgImage)

    smtp = smtplib.SMTP(SMTP_SERVER, smtp_port)
    smtp.sendmail(strFrom, strTo, msgRoot.as_string())
    smtp.quit()


def logger(level, message):

    log_base = {
        "log": {
            "log": {
                "level": level,
                "type": "grafanareporter"
            }
        }
    }
    log_base["log"]["log"]["message"] = message
    print(json.dumps(log_base))


def main():

    logger("info", f"generating time stamps")
    today = datetime.datetime.now()
    yesterday = (today - datetime.timedelta(days=1)).strftime('%Y-%m-%d')
    year, month, day = map(int, yesterday.split('-'))
    timefrom = int(datetime.datetime(year, month, day, 0, 0, 0).timestamp()) * 1000
    timeto = int(datetime.datetime(year, month, day, 23, 59, 59).timestamp()) * 1000

    time_parameter = f"&from={timefrom}&to={timeto}&kiosk"
    logger("info", f"time stamp for yesterday : {yesterday} - {time_parameter}")

    logger("info", f"Staring Chrome Driver")
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--window-size=1200,800')
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--disable-gpu')
    # chrome_options.add_argument("--window-size=1920,1080")
    driver = webdriver.Chrome(chrome_options=chrome_options)
    driver.get('https://grafana.rupeek.com')
    logger("info", "Loading grafana")

    GRAFANA_USERNAME = os.environ['GRAFANA_USERNAME']
    GRAFANA_PASSWORD = os.environ['GRAFANA_PASSWORD']

    driver.find_element(By.NAME, "user").send_keys(GRAFANA_USERNAME)
    driver.find_element(By.NAME, "password").send_keys(GRAFANA_PASSWORD)
    driver.find_element(By.XPATH, "//button[@type='submit']").click()

    logger("info", "Logged in to grafana")
    time.sleep(10)

    logger("info", "Fetching report list")
    report_list = os.environ['REPORT_LIST'].split(', ')
    logger("info", f"found following reports {report_list}")

    for report in report_list:
        report_dash_url = os.environ[report + "_" + 'DASHBOARD_URL'] + time_parameter
        report_email_sub = os.environ[report + "_" + 'EMAIL_SUBJECT']
        report_dash_timeout = int(
            os.environ.get(report + "_" + 'DASHBOARD_TIMEOUT', '30')
        )  # default time out is 30
        logger("info", f"Started processing: {report_email_sub} : {report_dash_url}")

        screenshot_dashboard(driver, report_dash_url, report, report_dash_timeout)
        mail_report(report, report_email_sub, report_dash_url, yesterday)

    logger("info", f"Stopping Chrome Driver")
    driver.quit()

if __name__ == '__main__':
    main()
