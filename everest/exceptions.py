"""
This file is part of the everest project. 
See LICENSE.txt for licensing, CONTRIBUTORS.txt for contributor information.

Created on Apr 13, 2010.
"""

from zope.schema import ValidationError # pylint: disable=E0611,F0401

__docformat__ = 'reStructuredText en'
__all__ = ['NotAnEmailAddress',
           'UnsupportedOperationException',
           ]


class NotAnEmailAddress(ValidationError): # pylint: disable=W0232
    """This is not a valid email address"""


class UnsupportedOperationException(Exception):
    """
    Raise this to indicate that the requested operation is not supported.
    """
