import logging
from smtplib import SMTP
from config import load_email_config
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from functools import wraps
from email_validator import validate_email, EmailNotValidError


def initialization_required(f):
    @wraps(f)
    def validate_email_service_initialization(*args, **kwargs):
        # first argument is instance of class
        instance = args[0]
        if not isinstance(instance, EmailService):
            raise ValueError("Email Service Decorator can only be bound to Email Service Instance Methods")
        
        if (not instance._initialized or not instance._smtp_config 
            or not instance._smtp_client_session):
            raise Exception(f"Invalid Email Service Configuration. Valid Initialization config is required. Error: {instance._init_error}")
        return f(*args, **kwargs)
    return validate_email_service_initialization


class EmailService:
    _initialized = False
    _init_error = None
    _smtp_config = {}
    _smtp_client_session = None
    _logger = None

    def __init__(self, config=None, raise_exception=False, connection_timeout=30, logger=None):
        self._initialized = True
        self._init_error = ""
        init_config = config or load_email_config()
        self._logger = logger or self.create_logger()

        required_settings = [
            "smtp_host",
            "smtp_port",
            "smtp_username",
            "smtp_password",
            "smtp_from_email"
        ]

        optional_settings = [
            ("smtp_use_tls", True),
            ("smtp_from_name", "Certificate Generator"),
            ("email_subject", "Certificated Successfully Generated"),
            ("email_template", ""),
        ]

        required_key_exc_msg = "Invalid Email Configuration. {} was not provided."
        for key in required_settings:
            if not init_config[key]:
                self._init_error = required_key_exc_msg.format(key)
                if raise_exception:
                    raise Exception(f"Email Service Initialization Error: {self._init_error}")
                break
            else:
                self._smtp_config[key] = init_config[key]

            if key == "smtp_from_email" and not self.validate_email_address(email=init_config[key], check_deliverability=True):
                self._init_error = "Invalid Email Configuration. Invalid from email address."
                if raise_exception:
                    raise Exception(f"Email Service Initialization Error: {self._init_error}")
                break

        for setting, default in optional_settings:
            if not init_config.get(setting):
                self._smtp_config[setting] = default
            else:
                self._smtp_config[setting] = init_config[setting]
        
        # call test connection to validate smtp configuration
        try:
            self._smtp_client_session = self.test_connection(connection_timeout)
            self._initialized = True
            self._init_error = None

        except Exception as e:
            self._initialized = False
            if raise_exception:
                raise e
            self._init_error = f"SMTP Connection Error, Invalid configuration. Exception: {str(e)}"
            self._logger.warning(self._init_error)

    def test_connection(self, connection_timeout=30):
        config = self._smtp_config
        client = SMTP(
            host=config["smtp_host"], port=config["smtp_port"], timeout=connection_timeout
        )

        if self._smtp_config.get("smtp_use_tls", True):
            client.starttls()

        client.login(user=config["smtp_username"], password=config["smtp_password"])

        return client

    @initialization_required
    def send_email(self, subject, body, recipient_email):
        try:
            email_address = self._smtp_config["smtp_from_email"]
            msg = MIMEMultipart()
            msg['From'] = self._smtp_config["smtp_from_name"]
            msg['To'] = recipient_email
            msg['Subject'] = subject
            msg.attach(MIMEText(body, 'plain'))

            self._smtp_client_session.sendmail(email_address, recipient_email, msg.as_string())

            self._logger.info("Email sent successfully!")
        except Exception as e:
            self._logger.exception(f"Failed to send email: {e}")


    def validate_email_address(self, email, check_deliverability=True): 
        try:
            validate_email(email, check_deliverability=check_deliverability)
            return True
        except EmailNotValidError as e:
            return False
    

    def create_logger(self):
        logger = logging.getLogger(__name__)
        logger.setLevel(logging.INFO)
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        return logger

    def __del__(self):
        if self._smtp_client_session:
            self._smtp_client_session.quit()
