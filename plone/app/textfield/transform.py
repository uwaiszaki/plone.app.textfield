# -*- coding: utf-8 -*-
from plone.app.textfield.interfaces import ITransformer
from plone.app.textfield.interfaces import TransformError
from Products.CMFCore.utils import getToolByName
from ZODB.POSException import ConflictError
from zope.component.hooks import getSite
from zope.interface import implementer

import logging
import six


LOG = logging.getLogger('plone.app.textfield')


@implementer(ITransformer)
class PortalTransformsTransformer(object):

    """Invoke portal_transforms to perform a conversion
    """

    def __init__(self, context):
        self.context = context

    def __call__(self, value, mimeType):
        # shortcut it we have no data
        if value.raw is None:
            return u''

        # shortcut if we already have the right value
        if mimeType is value.mimeType:
            return value.output

        site = getSite()

        transforms = getToolByName(site, 'portal_transforms', None)
        if transforms is None:
            raise TransformError("Cannot find portal_transforms tool")

        if six.PY2:
            # in Python 2 transforms expect str
            source_value = value.raw_encoded
        else:# in Python 3 we pass text
            source_value = value.raw

        try:
            data = transforms.convertTo(mimeType,
                                        source_value,
                                        mimetype=value.mimeType,
                                        context=self.context,
                                        # portal_transforms caches on this
                                        object=value._raw_holder,
                                        encoding=value.encoding)
            if data is None:
                # TODO: i18n
                msg = (u'No transform path found from "%s" to "%s".' %
                       (value.mimeType, mimeType))
                LOG.error(msg)
                # TODO: memoize?
                # plone_utils = getToolByName(self.context, 'plone_utils')
                # plone_utils.addPortalMessage(msg, type='error')
                # FIXME: message not always rendered, or rendered later on
                # other page.
                # The following might work better, but how to get the request?
                # IStatusMessage(request).add(msg, type='error')
                return u''

            else:
                output = data.getData()
                if six.PY2:
                    return output.decode(value.encoding)
                return output
        except ConflictError:
            raise
        except Exception as e:
            # log the traceback of the original exception
            LOG.error("Transform exception", exc_info=True)
            raise TransformError('Error during transformation', e)
