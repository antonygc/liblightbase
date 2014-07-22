from liblightbase import lbutils
from liblightbase.lbbase.struct import Base
from liblightbase.lbbase.metadata import BaseMetadata
from liblightbase.lbbase.content import Content
from liblightbase.lbbase.lbstruct.field import Field
from liblightbase.lbbase.lbstruct.group import Group
from liblightbase.lbbase.lbstruct.group import GroupMetadata

def json2base(jsonobj):
    """
    Convert a JSON string to liblightbase.lbbase.struct.Base object.
    @param jsonobj: JSON string.
    """
    return dict2base(dictobj=lbutils.json2object(jsonobj))

def base2json(base):
    """
    Convert a liblightbase.lbbase.struct.Base object to JSON string.
    @param jsonobj: JSON string.
    """
    return base.json

def json2document(base, jsonobj):
    """
    Convert a JSON string to BaseMetaClass object.
    @param base: liblightbae.lbbase.Base object
    @param jsonobj: JSON string.
    """
    return dict2document(base=base, dictobj=lbutils.json2object(jsonobj))

def document2json(base, document, **kw):
    """
    Convert a BaseMetaClass object to JSON string.
    @param document: BaseMetaClass object
    """
    return lbutils.object2json(document2dict(base, document), **kw)

def dict2base(dictobj):
    """
    Convert dictionary object to Base object
    @param dictobj: dictionary object
    """
    def assemble_content(content_object, dimension=0):
        """
        Parses content object and builds a list with Field and Group objects
        @param content_object:
        @param dimension:
        """
        content_list = Content()
        for obj in content_object:
            if obj.get('group'):
                group_metadata = GroupMetadata(**obj['group']['metadata'])
                _dimension = dimension
                if group_metadata.multivalued:
                    _dimension = _dimension + 1
                group_content = assemble_content(obj['group']['content'],
                        dimension=_dimension)
                group = Group(metadata = group_metadata,
                    content = group_content)
                content_list.append(group)
            elif obj.get('field'):
                field = Field(**obj['field'])
                if field.multivalued:
                    field.__dim__ = dimension + 1
                else:
                    field.__dim__ = dimension
                content_list.append(field)
        return content_list
    base_metadata = dictobj['metadata']
    base_content = assemble_content(dictobj['content'])
    base = Base(metadata=BaseMetadata(**base_metadata),
        content=base_content)
    return base

def dict2document(base, dictobj, metaclass=None):
    """
    Convert a dictionary object to BaseMetaClass object.
    @param dictobj: dictionary object.
    @param metaclass: GroupMetaClass in question.
    """
    if metaclass is None:
        metaclass = base.metaclass()
    kwargs = { }
    for member in dictobj:
        struct = base.get_struct(member)
        if struct.is_field:
            kwargs[member] = dictobj[member]
        elif struct.is_group:
            if struct.metadata.multivalued:
                meta_object = []
                for element in dictobj[member]:
                    meta_inner_object = dict2document(
                        base=base,
                        dictobj=element,
                        metaclass=base.get_metaclass(struct.metadata.name))
                    meta_object.append(meta_inner_object)
            else:
                meta_object = dict2document(
                    base=base,
                    dictobj=dictobj[member],
                    metaclass=base.get_metaclass(struct.metadata.name))
            kwargs[member] = meta_object
    return metaclass(**kwargs)

def document2dict(base, document, struct=None):
    """
    Convert a BaseMetaClass object to dictionary object.
    @param document: BaseMetaClass object
    @param struct: Field or Group object 
    """
    dictobj = { }
    if not struct: snames = base.content.__snames__
    else: snames = struct.content.__snames__
    for sname in snames:
        try: value = getattr(document, sname)
        except AttributeError: pass
        else:
            _struct = base.get_struct(sname)
            if _struct.is_field:
                dictobj[sname] = value
            elif _struct.is_group:
                if _struct.metadata.multivalued:
                    _value = [ ]
                    for element in value:
                        _value.append(document2dict(
                            base=base,
                            document=element,
                            struct=_struct))
                else:
                    _value = document2dict(
                        base=base,
                        document=value,
                        struct=_struct)
                dictobj[sname] = _value
    return dictobj
