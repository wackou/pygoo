PyGoo
==========================

PyGoo is an object-mapper for graph databases, such as `Neo4j`_.
It achieves the same goal as other object-mappers such as SQLAlchemy,
but uses graph databases as its backend.
It can also work as standalone mode, where there is no synchronization
with an underlying database but all the data is kept in memory.

*Note*: at the moment there is still no backend available, only in-memory graphs
are allowed

.. _`Neo4j`: http://neo4j.org

TODO: OneToMany is in fact OrderedList or UnorderedList (Set)
