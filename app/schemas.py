from marshmallow import Schema, fields


class AccountSchema(Schema):
    login = fields.String()
    password = fields.String()
    fullname = fields.String()
    phone = fields.String()
    access_token = fields.String(dump_only=True)
    message = fields.String(dump_only=True)


class ReportSchema(Schema):
    reports = fields.List(fields.Dict())
