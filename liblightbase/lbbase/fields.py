#!/usr/env python
# -*- coding: utf-8 -*-
import collections
import voluptuous
from liblightbase.lbtypes import standard
from liblightbase import lbcodecs


class Group():
    """
    This is the group definition
    """
    def __init__(self, name, alias, description, content, multivalued):
        """
        Group attributes
        """
        self.name = name
        self.alias = alias
        self.description = description
        self.content = content
        self.multivalued = multivalued
        self.json = lbcodecs.object2json(self)

    @property
    def is_group(self):
        return True

    @property
    def is_field(self):
        return False

    @property
    def content(self):
        return self._content

    @content.setter
    def content(self, c):

        content_list = [ ]
        self.__names__ = [ ]

        if type(c) is list:
            for value in c:

                if isinstance(value, Field):
                    self.__names__.append(value.name)

                elif isinstance(value, Group):
                    self.__names__.append(value.name)
                    self.__names__ = self.__names__ + value.__names__
                else:
                    msg = 'InstanceError This should be an instance of Field or Group. instead it is %s' % value
                    raise Exception(msg)

                content_list.append(value)

            repeated_names = [x for x, y in collections.Counter(self.__names__).items() if y > 1]
            if len(repeated_names) > 0:
                raise Exception('Base cannot have repeated names : %s' % str(repeated_names))

            self._content = content_list
        else:
            msg = 'Type Error: content must be a list instead of %s' % c
            raise Exception(msg)
            self._content = None

    @property
    def multivalued(self):
        return self._multivalued.multivalued

    @multivalued.setter
    def multivalued(self, m):
        if isinstance(m, Multivalued):
            self._multivalued = m
        else:
            # Invalid multivalued. Raise exception
            msg = 'InstanceError This should be an instance of Multivalued. instead it is %s' % m
            raise Exception(msg)
            self._multivalued = None

    @property
    def object(self):
        """ Builds group object
        """
        return dict(
            group = dict(
                content = [attr.object for attr in self.content],
                metadata = dict(
                    name = self.name,
                    alias = self.alias,
                    description = self.description,
                    multivalued =  self.multivalued
                )
            )
        )

    def schema(self, base, id):
        """ Builds base schema
        """
        _schema = dict()
        for attr in self.content:
            required = getattr(attr, 'required', False)
            if required is True:
                _schema[voluptuous.Required(attr.name)] = attr.schema(base, id)
            else:
                _schema[attr.name] = attr.schema(base, id)
        if self.multivalued is True:
            return [_schema]
        elif self.multivalued is False:
            return _schema

    def reg_model(self, base):
        """ Builds registry model
        """
        _schema = dict()
        for attr in self.content:
            _schema[attr.name] = attr.reg_model(base)
        if self.multivalued is True:
            return [_schema]
        elif self.multivalued is False:
            return _schema

    @property
    def relational_fields(self):
        """ Get relational fields
        """
        rel_fields = { }

        for struct in self.content:
            if isinstance(struct, Field) and struct.is_rel:
                rel_fields[struct.name] = struct
            elif isinstance(struct, Group):
                rel_fields.update(struct.relational_fields)

        return rel_fields

    def _encoded(self):
        """
        Serialize Groups data
        """
        return self.__dict__


class Field():
    """
    This is the field description
    """
    def __init__(self, name, alias, description, datatype, indices, multivalued, required):
        """
        Field attributes
        """
        self.name = name
        self.alias = alias
        self.description = description
        self.datatype = datatype
        self.indices = indices
        self.multivalued = multivalued
        self.required = required
        self.json = lbcodecs.object2json(self)

    @property
    def is_group(self):
        return False

    @property
    def is_field(self):
        return True

    @property
    def datatype(self):
          return self._datatype.datatype

    @datatype.setter
    def datatype(self, t):
        """
        check this attribute properties
        """
        if isinstance(t, DataType):
            self._datatype = t
        else:
            msg = 'TypeError This must be a instance of datatype. Instead it is %s' % t
            raise Exception(msg)
            self._datatype = None

    @property
    def indices(self):
        return [index.index for index in self._indices]

    @indices.setter
    def indices(self, i):
        """
        Validate the value for this field
        """
        indices_list = list()
        if type(i) is list:
            for value in i:
                if isinstance(value, Index):
                    indices_list.append(value)
                else:
                    msg = 'InstanceError This should be an instance of Indice. instead it is %s' % value
                    raise Exception(msg)
            self._indices = indices_list
        else:
            # Invalid index. Raise exception
            self._indices = None
            msg = 'Type Error: indexes must be a list instead of %s' % i
            raise Exception(msg)


    @property
    def multivalued(self):
        return self._multivalued.multivalued

    @multivalued.setter
    def multivalued(self, m):
        if isinstance(m, Multivalued):
            self._multivalued = m
        else:
            # Invalid multivalued. Raise exception
            msg = 'InstanceError This should be an instance of Multivalued. instead it is %s' % m
            raise Exception(msg)
            self._multivalued = None

    @property
    def required(self):
        return self._required.required

    @required.setter
    def required(self, r):
        if isinstance(r, Required):
            self._required = r
        else:
            # Invalid required. Raise exception
            msg = 'InstanceError This should be an instance of Required. instead it is %s' % r
            raise Exception(msg)
            self._required = None

    @property
    def object(self):
        """ Builds field object
        """
        _field = dict(
            name = self.name,
            alias = self.alias,
            description = self.description,
            indices = self.indices,
            datatype = self.datatype,
            multivalued = self.multivalued,
            required = self.required
        )
        return dict(field = _field)

    def schema(self, base, id=None):
        """ Builds field schema
        """
        datatype = self.datatype.__schema__

        if self.multivalued is True:
            return [datatype(base, self, id)]
        elif self.multivalued is False:
            return datatype(base, self, id)
        else:
            raise Exception('multivalued must be boolean')

    def reg_model(self, base):
        """ Builds registry model
        """
        return self.schema(base)

    @property
    def is_rel(self):
        """ Check if field is relational
        """
        is_rel = set(['Ordenado', 'Vazio', 'Unico'])
        if len(is_rel.intersection(self.indices)) > 0:
            return True
        return False

    def _encoded(self):
        """
        Encode data for JSON
        """
        return self.__dict__


class Index():
    """
    This is the index object.
    """
    def __init__(self, index):
        self.index = index
        self.json = lbcodecs.object2json(self)

    def valid_indices(self):
        """
        Returns a list of valid values for indices
        valid_indices = [
            'None',
            'Textual',
            'Ordered',
            'Unique',
            'Fonetic',
            'Fuzzy',
            'Empty',
        ]
        """
        valid_indices = [
            'Nenhum',
            'Textual',
            'Ordenado',
            'Unico',
            'Fonetico',
            'Fuzzy',
            'Vazio',
        ]

        return valid_indices

    @property
    def index(self):
        return self._index

    @index.setter
    def index(self, i):
        if not i in self.valid_indices():
            # invalid value for indices. Raise exception
            self._index = None
            msg = 'IndexError violation. Supplied value for index %s is not valid' % i
            raise Exception(msg)

        self._index = i

    def _encoded(self):
        """
        Encode data for JSON
        """

        return self.index

class DataType():
    """
    Define valid data type
    """
    def __init__(self, datatype):
        self.datatype = datatype
        self.__schema__ = getattr(standard, self.datatype)
        self.json = lbcodecs.object2json(self)

    def valid_types(self):
        """
        Get valid instances of datatypes
        """
        valid_datatypes = [
            'Boolean',
            'Date',
            'DateTime',
            'Decimal',
            'Document',
            'Email',
            'File',
            'Html',
            'Image',
            'Integer',
            'Json',
            'Money',
            'Password',
            'SelfEnumerated',
            'Sound',
            'Text',
            'TextArea',
            'Time',
            'Url',
            'Video'
        ]
        return valid_datatypes

    @property
    def datatype(self):
        return self._datatype

    @datatype.setter
    def datatype(self, t):
        """
        Check if is a valid datatype
        """
        if t in self.valid_types():
            self._datatype = t
        else:
            msg = 'TypeError Wrong DataType. The value you supllied is not valid: %s' % t
            raise Exception(msg)
            self._datatype = None

    def _encoded(self):
        """
        Encode data for JSON
        """

        return self.datatype

class Multivalued():
    """
    Define valid multivalued
    """
    def __init__(self, multivalued):
        self.multivalued = multivalued

    @property
    def multivalued(self):
        return self._multivalued

    @multivalued.setter
    def multivalued(self, m):
        """
        Check if is a valid multivalued
        """
        if isinstance(m, bool):
            self._multivalued = m
        else:
            msg = 'TypeError Wrong multivalued. The value you supllied for multivalued is not valid: %s' % m
            raise Exception(msg)
            self._multivalued = None


class Required():
    """
    Define valid required
    """
    def __init__(self, required):
        self.required = required

    @property
    def required(self):
        return self._required

    @required.setter
    def required(self, r):
        """
        Check if is a valid required
        """
        if isinstance(r, bool):
            self._required= r
        else:
            msg = 'TypeError Wrong required. The value you supllied for required is not valid: %s' % r
            raise Exception(msg)
            self._required = None
