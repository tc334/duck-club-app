from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from flask import current_app


def send_email(to, subject, template):
    message = Mail(
        from_email='tegan.counts@gmail.com',
        to_emails=to,
        subject=subject,
        html_content=template)
    try:
        print(f"Alpha:{current_app.config['SENDGRID_API_KEY']}")
        sg = SendGridAPIClient(current_app.config["SENDGRID_API_KEY"])
        response = sg.send(message)
        print(response.status_code)
        print(response.body)
        print(response.headers)
    except Exception as e:
        print(e)
