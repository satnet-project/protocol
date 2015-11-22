# coding=utf-8
"""
   Copyright 2015 Samuel Góngora García

   Licensed under the Apache License, Version 2.0 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.
"""
__author__ = 's.gongoragarcia@gmail.com'

import pytz
import datetime
import dateutil.parser


def localize_datetime_utc(date_time):
    """
    Localizes in the UTC timezone a given Datetime object.
    :param date_time: The object to be localized.
    :return: Localized Datetime object in the UTC timezone.
    """
    return pytz.utc.localize(date_time)


def serialize_iso8601_date(dt):
    """
    From a localized datetime.datetime object, it returns the section that
    contains the date together with the timezone.
    :param dt: datetime.datetime object.
    :return: Date and TimeZone in ISO8601 format.
    """
    if isinstance(dt, datetime.datetime):
        return dt.replace(hour=0, minute=0, second=0).isoformat()

    if isinstance(dt, datetime.date):
        return pytz.utc.localize(datetime.datetime.combine(
            dt, datetime.time(0, 0, 0))
        ).isoformat()

    raise TypeError(
        '<dt> should be either datetime.datetime or datetime.date'
    )


def deserialize_iso8601_date(iso8601_date):
    """
    Deserializes an ISO-8601 date string into a datetime.datetime object, UTC
    localized.
    :param iso8601_date: ISO-8601 string.
    :return: datetime.datetime object.
    """
    return dateutil.parser.parse(iso8601_date).astimezone(pytz.utc)


def serialize_iso8601_time(t):
    """
    From a localized datetime.datetime object, it returns the section that
    contains the time together with the timezone.
    :param t: datetime.datetime object.
    :return: Time and TimeZone in ISO8601 format.
    """
    if isinstance(t, datetime.datetime):
        return t.isoformat().split('T')[1]

    if isinstance(t, datetime.time):
        if t.tzinfo is None:
            return t.isoformat() + '+00:00'
        else:
            return t.isoformat()

    raise TypeError(
        '<dt> should be either datetime.datetime or datetime.date'
    )


def deserialize_iso8601_time(iso8601_time):
    """
    Deserializes an ISO-8601 time string into a datetime.datetime object.
    :param iso8601_time: ISO-8601 string.
    :return: datetime.datetime object.
    """
    return dateutil.parser.parse(iso8601_time).astimezone(
        pytz.utc
    ).replace(tzinfo=None).timetz()