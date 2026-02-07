from services.email import EmailService

email_service = EmailService()
email_service.send_email("Test Email", "Hello World", "test@gmail.com")