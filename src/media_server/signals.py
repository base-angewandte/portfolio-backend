from django import dispatch

media_order_update = dispatch.Signal(providing_args=['entry_id'])
