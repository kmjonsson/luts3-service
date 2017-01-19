"""
Host scale factor updater.

This module will connect to the database (once available), and update the
scaling factors, in the database.

Author: Henrik Thostrup Jensen <htj@ndgf.org>
Copyright: Nordic Data Grid Facility (2010)
"""

from twisted.python import log
from twisted.internet import defer
from twisted.application import service



TRUNCATE_HOST_SCALE_FACTOR = '''TRUNCATE TABLE hostscalefactors'''
INSERT_HOST_SCALE_FACTOR   = '''INSERT INTO hostscalefactors (machine_name, scale_factor) VALUES (%s, %s)'''

# scale options
SCALE_BLOCK      = 'hostscaling'

class HostScaleFactorUpdater(service.Service):

    def __init__(self, cfg, db):
        self.pool_proxy = db.pool_proxy

        # get scale factors
        self.scale_factors = {}
        
        if not SCALE_BLOCK in cfg.sections():
            return
        
        for hostname in cfg.options(SCALE_BLOCK):
            try:
                self.scale_factors[hostname] = cfg.getfloat(SCALE_BLOCK, hostname)
            except ValueError:
                log.msg('Invalid scale factor value for entry: %s' % hostname, system='sgas.Setup')


    def startService(self):
        service.Service.startService(self)
        return self.updateScaleFactors()


    def stopService(self):
        service.Service.stopService(self)
        return defer.succeed(None)


    @defer.inlineCallbacks
    def updateScaleFactors(self):
        try:
            yield self.pool_proxy.dbpool.runInteraction(self.issueUpdateStatements)
            log.msg("Host scale factors updated (%i entries)" % len(self.scale_factors), system='sgas.HostScaleFactorUpdate')
        except Exception, e:
            log.msg('Error updating host scale factors. Message: %s' % str(e), system='sgas.HostScaleFactorUpdate')


    def issueUpdateStatements(self, txn):
        # executed in seperate thread, so it is safe to block

        update_args = [ (hostname, scale_value) for hostname, scale_value in self.scale_factors.items() ]

        # clear "old" scale factor and replace with new ones from configuration
        # this is most likely the same as the ones that exists in the database,
        # but it is a cheap operation, and logic is simple
        txn.execute(TRUNCATE_HOST_SCALE_FACTOR)
        txn.executemany(INSERT_HOST_SCALE_FACTOR, update_args)

