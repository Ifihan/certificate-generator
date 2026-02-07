from marshmallow import fields, Schema, validate

class EmailSettingsSchema(Schema):
    smtp_host = fields.Str(required=True)
    smtp_port = fields.Str(required=True, validate=validate.Regexp("^[0-9]+$"))
    smtp_username = fields.Str(required=True)
    smtp_password = fields.Str(required=True)
    smtp_from_email = fields.Str(required=True)

    smtp_from_name = fields.Str()
    smtp_use_tls = fields.Bool()
    email_subject = fields.Str()
    email_template = fields.Str()

    enable_email = fields.Bool()
    email_column_name = fields.Str()


class SendTestEmailSchema(Schema):
    recipient_email = fields.Email(required=True)
    from_name = fields.Str(required=False)
    subject = fields.Str(required=False)
    body = fields.Str(required=False)