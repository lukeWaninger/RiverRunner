================
Data Abstraction
================

This application is built with future scalability in mind. With that, we chose to implement our back-end interface
with `sqlalchemy`'s ORM features giving us flexibility as we move forward.

.. toctree::
   :maxdepth: 2

.. autoclass:: riverrunner.Context

Note: Although the __init__ functions are not defined for each ORM mapping object below, you may initialize any attribute using standard constructor-argument initialization.
        ::

            address = Address(city='Seattle', state='WA', zip='98112', ...)
            prediction = Prediction()

.. automodule:: riverrunner.context
   :members:
   :member-order: bysource
   :exclude-members: Context
