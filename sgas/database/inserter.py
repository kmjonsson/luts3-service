"""
UR insert logic.

Should probably have its own top level module.

Author: Henrik Thostrup Jensen <htj@ndgf.org>

Copyright: Nordic Data Grid Facility (2010)
"""

import time

from twisted.internet import defer

from sgas.usagerecord import ursplitter, urparser
from sgas.authz import rights
from sgas.database import error



def insertRecords(usagerecord_data, db, authorizer, insert_identity=None, insert_hostname=None):

    # parse ur data
    insert_time = time.gmtime()

    ur_docs = []

    for ur_element in ursplitter.splitURDocument(usagerecord_data):
        ur_doc = urparser.xmlToDict(ur_element,
                                    insert_identity=insert_identity,
                                    insert_hostname=insert_hostname,
                                    insert_time=insert_time)
        ur_docs.append(ur_doc)

    # check authz
    machine_names = set( [ doc.get('machine_name') for doc in ur_docs ] )
    ctx = [ ('machine_name', mn) for mn in machine_names ]

    if authorizer.isAllowed(insert_identity, rights.ACTION_INSERT, ctx):
        # insert records, if allowed
        return db.insert(ur_docs)
    else:
        MSG = 'Subject %s is not allowed to perform insertion for machines: %s' % (insert_identity, ','.join(machine_names))
        return defer.fail(error.SecurityError(MSG))

