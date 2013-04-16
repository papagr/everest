"""
Entity and aggregate base classes.

This file is part of the everest project. 
See LICENSE.txt for licensing, CONTRIBUTORS.txt for contributor information.

Created on May 12, 2011.
"""
from everest.constants import CASCADES
from everest.entities.interfaces import IAggregate
from everest.entities.interfaces import IEntity
from everest.entities.traversal import AddingDomainVisitor
from everest.entities.traversal import DomainTreeTraverser
from everest.entities.traversal import RemovingDomainVisitor
from everest.querying.utils import get_filter_specification_factory
from everest.utils import get_filter_specification_visitor
from everest.utils import get_order_specification_visitor
from zope.interface import implements # pylint: disable=E0611,F0401

__docformat__ = 'reStructuredText en'
__all__ = ['Aggregate',
           'Entity',
           ]


class Entity(object):
    """
    Abstract base class for all model entities.

    All entities have an ID which is used as the default value for equality
    comparison. The object may be initialized without an ID.
    """
    implements(IEntity)

    id = None

    def __init__(self, id=None): # redefining id pylint: disable=W0622
        if self.__class__ is Entity:
            raise NotImplementedError('Abstract class.')
        if not id is None:
            self.id = id

    @property
    def slug(self):
        """
        Returns a human-readable and URL-compatible string that is unique
        within all siblings of this entity.
        """
        return None if self.id is None else str(self.id)

    @classmethod
    def create_from_data(cls, data):
        return cls(**data)

    def __eq__(self, other):
        return isinstance(other, self.__class__) \
               and self.id == other.id \
               and not (self.id is None and other.id is None)

    def __ne__(self, other):
        return not self.__eq__(other)


class Aggregate(object):
    """
    Abstract base class for aggregates.

    An aggregate is an accessor for a set of entities of the same type which 
    are held in some repository. 

    Supports filtering, sorting, slicing, counting, iteration as well as
    retrieving, adding and removing entities.
    """
    implements(IAggregate)

    #: Entity class (type) of the entities in this aggregate.
    entity_class = None

    def __init__(self):
        if self.__class__ is Aggregate:
            raise NotImplementedError('Abstract class.')
        #: Specification for filtering
        #: (:class:`everest.querying.specifications.FilterSpecification`).
        #: Attribute names in this specification are relative to the entity.
        self._filter_spec = None
        #: Specification for ordering
        #: (:class:`everest.querying.specifications.OrderSpecification`).
        #: Attribute names in this specification are relative to the entity.
        self._order_spec = None
        #: Key for slicing. (:type:`slice`).
        self._slice_key = None

    def clone(self):
        """
        Returns a clone of this aggregate.
        """
        clone = self.__class__.__new__(self.__class__)
        # access protected member pylint: disable=W0212
        clone._filter_spec = self._filter_spec
        clone._order_spec = self._order_spec
        clone._slice_key = self._slice_key
        # pylint: enable=W0212
        return clone

    def iterator(self):
        """
        Returns an iterator for the entities contained in the underlying
        aggregate.

        If specified, filter, order, and slice settings are applied.

        :returns: an iterator for the aggregate entities
        """
        return iter(self._get_data_query())

    def __iter__(self):
        return self.iterator()

    def count(self):
        """
        Returns the total number of entities in the underlying aggregate.
        If specified, filter specs are applied. A specified slice key is
        ignored.

        :returns: number of aggregate members (:class:`int`)
        """
        return self._get_filtered_query(None).count()

    def get_by_id(self, id_key):
        """
        Returns an entity by ID  or `None` if the entity is not found.

        :note: if a filter is set which matches the requested entity, it
          will not be found.
        :param id_key: ID value to look up
        :type id_key: `int` or `str`
        :raises: :class:`everest.exceptions.MultipleResultsException` if more
          than one entity is found for the given ID value. 
        :returns: specified entity or `None`
        """
        raise NotImplementedError('Abstract method.')

    def get_by_slug(self, slug):
        """
        Returns an entity by slug or `None` if the entity is not found.

        :note: if a filter is set which matches the requested entity, it
          will not be found.
        :param slug: slug value to look up
        :type slug: `str`
        :raises: :class:`everest.exceptions.MultipleResultsException` if more
          than one entity is found for the given ID value. 
        :returns: entity or `None`
        """
        raise NotImplementedError('Abstract method.')

    def add(self, entity):
        """
        Adds an entity to the aggregate.

        If the entity has an ID, it must be unique within the aggregate.

        :param entity: entity (domain object) to add
        :type entity: object implementing
          :class:`everest.entities.interfaces.IEntity`
        :raise ValueError: if an entity with the same ID exists
        """
        raise NotImplementedError('Abstract method.')

    def remove(self, entity):
        """
        Removes an entity from the aggregate.

        :param entity: entity (domain object) to remove.
        :type entity: object implementing
          :class:`everest.entities.interfaces.IEntity`
        :raise ValueError: entity was not found
        """
        raise NotImplementedError('Abstract method.')

    def update(self, entity):
        """
        Updates the existing entity with the same ID as the given entity 
        with the state of the latter.
        
        Relies on the underlying repository for the implementation of the
        state update.
        
        :param entity: entity (domain object) to transfer state to.
        :type entity: object implementing
          :class:`everest.entities.interfaces.IEntity`
        :param source_entity: source entity to transfer state from. 
        :type source_entity: object implementing
          :class:`everest.entities.interfaces.IEntity`
        """
        raise NotImplementedError('Abstract method.')

    def query(self):
        """
        Returns a query for this aggregate.
        """
        raise NotImplementedError('Abstract method.')

    @property
    def expression_kind(self):
        """
        Returns the kind of filter and order expression this aggregate builds.
        """
        raise NotImplementedError('Abstract property.')

    def get_root_aggregate(self, rc):
        """
        Returns a root aggregate for the given registered resource. 
        
        The aggregate is retrieved from the same repository that was used to
        create this aggregate.
        """
        raise NotImplementedError('Abstract method.')

    def _get_filter(self):
        #: Returns the filter specification for this aggregate.
        return self._filter_spec

    def _set_filter(self, filter_spec):
        #: Sets the filter specification for this aggregate.
        self._filter_spec = filter_spec

    filter = property(_get_filter, _set_filter)

    def _get_order(self):
        #: Returns the order specification for this aggregate.
        return self._order_spec

    def _set_order(self, order_spec):
        #: Sets the order specification for this aggregate.
        self._order_spec = order_spec

    order = property(_get_order, _set_order)

    def _get_slice(self):
        #: Returns the slice key for this aggregate.
        return self._slice_key

    def _set_slice(self, slice_key):
        #: Sets the slice key for this aggregate. Filter and order specs
        #: are applied before the slicing operation is performed.
        self._slice_key = slice_key

    slice = property(_get_slice, _set_slice)

    def _query_optimizer(self, query, slice_key): # unused pylint: disable=W0613
        """
        Override this to generate optimized queries based on the given
        slice key.
        
        This default implementation just returns the given query as is.
        
        :param query: query to optimize as returned from the data source.
        :param key: slice key to use for the query or `None`, if no slicing
          was applied.
        """
        return query

    def _get_filtered_query(self, key):
        #: Returns a query filtered by the current filter specification.
        query = self._query_optimizer(self.query(), key)
        if not self.filter is None:
            visitor_cls = \
              get_filter_specification_visitor(self.expression_kind)
            vst = visitor_cls(self.entity_class)
            self.filter.accept(vst)
            query = vst.filter_query(query)
        return query

    def _get_ordered_query(self, key):
        #: Returns a filtered query ordered by the current order
        #: specification.
        query = self._get_filtered_query(key)
        if not self._order_spec is None:
            #: Orders the given query with the given order specification.
            visitor_cls = \
              get_order_specification_visitor(self.expression_kind)
            vst = visitor_cls(self.entity_class)
            self._order_spec.accept(vst)
            query = vst.order_query(query)
        return query

    def _get_data_query(self):
        #: Returns an ordered query sliced by the current slice key.
        query = self._get_ordered_query(self._slice_key)
        if not self._slice_key is None:
            query = query.slice(self._slice_key.start,
                                self._slice_key.stop)
        return query


class RootAggregate(Aggregate):
    """
    Abstract base class for root aggregates.

    A root aggregate provides access to all entities in an underlying
    repository.
    """

    #: This holds the value for the expression_kind property (the kind of
    #: filter and order expression this root aggregate builds).
    _expression_kind = None

    def __init__(self, entity_class, session_factory, repository):
        """
        Constructor.

        :param entity_class: The entity class (type) of the entities in this
            aggregate.
        :type entity_class: A class implementing
            :class:`everest.entities.interfaces.IEntity`.
        :param session_factory: The session factory for this aggregate.
        :param repository: The repository that created this aggregate. 
        """
        if self.__class__ is RootAggregate:
            raise NotImplementedError('Abstract class.')
        Aggregate.__init__(self)
        #: The entity class managed by this aggregate.
        self.entity_class = entity_class
        #: The session factory.
        self._session_factory = session_factory
        #
        self.__repository = repository

    @classmethod
    def create(cls, entity_class, session_factory, repository):
        """
        Factory class method to create a new aggregate.
        """
        return cls(entity_class, session_factory, repository)

    def clone(self):
        clone = Aggregate.clone(self)
        clone.entity_class = self.entity_class
         # protected pylint: disable=W0212
        clone._session_factory = self._session_factory
        clone.__repository = self.__repository
         # enable=W0212
        return clone

    def get_by_id(self, id_key):
        ent = self._session.get_by_id(self.entity_class, id_key)
        if ent is None:
            ent = self._query_by_id(id_key)
        if not ent is None \
           and not self._filter_spec is None \
           and not self._filter_spec.is_satisfied_by(ent):
            ent = None
        return ent

    def get_by_slug(self, slug):
        raise NotImplementedError('Abstract method.')

    def add(self, entity):
        if not isinstance(entity, self.entity_class):
            raise ValueError('Can only add entities of type "%s" to this '
                             'aggregate.' % self.entity_class)
        trv = DomainTreeTraverser(entity)
        vst = AddingDomainVisitor(self, self._session)
        trv.run(vst)

    def remove(self, entity):
        trv = DomainTreeTraverser(entity)
        vst = RemovingDomainVisitor(self, self._session)
        trv.run(vst)

    def update(self, entity):
        return self._session.update(self.entity_class, entity)

    def query(self):
        return self._session.query(self.entity_class)

    @property
    def expression_kind(self):
        return self._expression_kind

    def get_root_aggregate(self, rc):
        return self.__repository.get_aggregate(rc)

    def make_relationship_aggregate(self, relationship):
        """
        Returns a new relationship aggregate for the given relationship.
        
        :param relationship: instance of 
          :class:`everest.relationship.ReferencedRelateeRelationship` or
          :class:`everest.relationship.BackreferencedRelatorRelationship`
        """
        return RelationshipAggregate(self, relationship)

    def _query_by_id(self, id_key):
        raise NotImplementedError('Abstract method.')

    @property
    def _session(self):
        return self._session_factory()


class RelationshipAggregate(Aggregate):
    """
    An aggregate that references a subset of a root aggregate defined through
    a relationship.
    """
    def __init__(self, root_aggregate, relationship):
        Aggregate.__init__(self)
        self._root_aggregate = root_aggregate
        self._relationship = relationship

    def get_by_id(self, id_key):
        ent = self._root_aggregate.get_by_id(id_key)
        if not ent is None and not self.filter.is_satisfied_by(ent):
            ent = None
        return ent

    def get_by_slug(self, slug):
        ent = self._root_aggregate.get_by_slug(slug)
        if not ent is None and not self.filter.is_satisfied_by(ent):
            ent = None
        return ent

    def query(self):
        return self._root_aggregate.query()

    @property
    def entity_class(self):
        return self._root_aggregate.entity_class

    @property
    def expression_kind(self):
        return self._root_aggregate.expression_kind

    def get_root_aggregate(self, rc):
        return self._root_aggregate.get_root_aggregate(rc)

    def update(self, entity):
        return self._root_aggregate.update(entity)

    def add(self, entity):
        self._relationship.add(entity)
        if self._relationship.descriptor.cascade & CASCADES.ADD \
           and (entity.id is None
                or self._root_aggregate.get_by_id(entity.id) is None):
            self._root_aggregate.add(entity)

    def remove(self, entity):
        if self._relationship.descriptor.cascade & CASCADES.DELETE \
           and (not entity.id is None
                and not self._root_aggregate.get_by_id(entity.id) is None):
            self._root_aggregate.remove(entity)
        self._relationship.remove(entity)

    def _get_filter(self):
        # Overwrite to prepend relationship specification to filter spec.
        rel_spec = self._relationship.specification
        if not self._filter_spec is None:
            spec_fac = get_filter_specification_factory()
            filter_spec = spec_fac.create_conjunction(rel_spec,
                                                      self._filter_spec)
        else:
            filter_spec = rel_spec
        return filter_spec

    filter = property(_get_filter, Aggregate._set_filter)
