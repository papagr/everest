"""
This file is part of the everest project. 
See LICENSE.txt for licensing, CONTRIBUTORS.txt for contributor information.

Created on Jun 14, 2012.
"""
from everest.resources.utils import get_registered_collection_resources
from everest.resources.utils import get_resource_url
from everest.resources.utils import provides_collection_resource
from everest.resources.utils import provides_member_resource
from everest.resources.utils import provides_resource
from everest.testing import ResourceTestCase
from everest.tests.testapp_db.testing import create_collection

__docformat__ = 'reStructuredText en'
__all__ = ['ResourcesUtilsTestCase',
           ]


class ResourcesUtilsTestCase(ResourceTestCase):
    package_name = 'everest.tests.testapp_db'
    config_file_name = 'configure_no_orm.zcml'

    def test_get_resource_url(self):
        coll = create_collection()
        url = get_resource_url(coll)
        self.assert_not_equal(url.find('/my-entities'), -1)

    def test_provides_resource(self):
        coll = create_collection()
        mb = iter(coll).next()
        self.assert_true(provides_member_resource(type(mb)))
        self.assert_true(provides_member_resource(mb))
        self.assert_false(provides_member_resource(coll))
        self.assert_true(provides_resource(type(mb)))
        self.assert_true(provides_resource(mb))
        self.assert_true(provides_collection_resource(type(coll)))
        self.assert_true(provides_collection_resource(coll))
        self.assert_false(provides_collection_resource(mb))
        self.assert_true(provides_resource(type(coll)))
        self.assert_true(provides_resource(coll))
        self.assert_false(provides_resource(mb.get_entity()))

    def test_get_registered_collection_resources(self):
        colls = get_registered_collection_resources()
        self.assert_equal(len(colls), 5)