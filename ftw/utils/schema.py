#!/usr/bin/env python
# -*- coding: utf-8 -*-

from marshmallow import Schema, fields, EXCLUDE


class DockerSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    container_id = fields.Str(missing="-")
    user = fields.Str()
    create = fields.Str()
    pwd = fields.Str()
    method = fields.Str()
    port = fields.Int()
    more_sec = fields.Str(missing="-")
    note = fields.Str(missing="-")


class SockSchema(DockerSchema):
    type = fields.Str(default="ss")


class V2raySchema(DockerSchema):
    class Meta:
        # fields = ("id", "alterId", "usr", "ct")
        unknown = EXCLUDE

    pwd = fields.Function(lambda obj: obj["id"])
    method = fields.Function(lambda obj: obj["alterId"])
    user = fields.Function(lambda obj: obj["_metadata"]["usr"])
    create = fields.Function(lambda obj: obj["_metadata"]["ct"])
    port = fields.Function(lambda obj: obj.get("port", 443))

    type = fields.Str(default="vmess")
