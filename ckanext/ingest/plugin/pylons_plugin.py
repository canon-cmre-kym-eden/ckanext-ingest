# -*- coding: utf-8 -*-

import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit

class IngestPylonsPlugin(plugins.SingletonPlugin):
    '''Pylons-specific implementation'''
    print('Pylons loaded')
