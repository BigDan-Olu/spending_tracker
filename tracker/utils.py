import os

import requests


def send_brevo_email(to_email, subject, html_content):

    url = "https://api.brevo.com/v3/smtp/email"

    headers = {
        "accept": "application/json",
        "api-key": os.getenv("BREVO_API_KEY"),
        "content-type": "application/json",
    }

    payload = {
        "sender": {
            "name": "Spending Tracker",
            "email": "dabidewon@gmail.com",
        },
        "to": [{"email": to_email}],
        "subject": subject,
        "htmlContent": html_content,
    }

    response = requests.post(url, json=payload, headers=headers)

    print("BREVO STATUS:", response.status_code)
    print("BREVO BODY:", response.text)

    return response
