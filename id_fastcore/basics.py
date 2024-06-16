# AUTOGENERATED! DO NOT EDIT! File to edit: ../nbs/01_basics.ipynb.

# %% auto 0
__all__ = ['defaults', 'null', 'ifnone', 'maybe_attr', 'basic_repr', 'is_array', 'listify', 'tuplify', 'true', 'NullType',
           'tonull', 'get_class', 'mk_class', 'wrap_class', 'ignore_exceptions', 'exec_local', 'risinstance', 'Inf',
           'in_', 'ret_true', 'ret_false', 'stop', 'gen', 'chunked', 'otherwise', 'custom_dir', 'AttrDict', 'NS',
           'partition', 'flatten', 'concat', 'strcat', 'detuplify', 'replicate', 'setify', 'merge', 'range_of',
           'groupby', 'last_index', 'filter_dict', 'filter_keys', 'filter_values', 'cycle', 'zip_cycle', 'sorted_ex',
           'not_', 'argwhere', 'filter_ex', 'renumerate', 'only', 'lt', 'gt', 'le', 'ge', 'eq', 'ne', 'add', 'sub',
           'mul', 'truediv', 'is_', 'is_not', 'mod']

# %% ../nbs/01_basics.ipynb 1
from .imports import *
import builtins, types
import pprint
try: from types import Union
except ImportError: Union = None

# %% ../nbs/01_basics.ipynb 5
defaults = SimpleNamespace()

# %% ../nbs/01_basics.ipynb 7
def ifnone(a, b):
    "`b` if `a` is None else `a`"
    return b if a is None else a

# %% ../nbs/01_basics.ipynb 10
def maybe_attr(o, attr):
    "`getattr(o,attr,o)`"
    return getattr(o, attr, o)

# %% ../nbs/01_basics.ipynb 13
def basic_repr(flds=None):
    "Minimal `__repr__`"
    if isinstance(flds, str): flds = re.split(', *', flds)
    flds = list(flds or [])
    def _f(self):
        res = f'{type(self).__module__}.{type(self).__name__}'
        if not flds: return f'<{res}>'
        sig = ', '.join(f'{o} = {getattr(self, o)!r}' for o in flds)
        return f'{res}({sig})'
    return _f

# %% ../nbs/01_basics.ipynb 19
def is_array(x):
    "`True` if `x` supports `__array__` or `iloc`"
    return hasattr(x, '__array__') or hasattr(x, 'iloc')

# %% ../nbs/01_basics.ipynb 21
def listify(o=None, *rest, use_list=False, match=None):
    "Convert `o` to a `list`"
    if rest: o = (o,) + rest
    # if use_list - shortcut to [o]
    if use_list: res = list(o)
    elif o is None: res = []
    elif isinstance(o, list): res = o
    elif isinstance(o, str) or is_array(o): res = [o]
    elif is_iter(o): res = list(o)
    else: res = [o]
    if match is not None:
        if is_coll(match): match = len(match)
        if len(res) == 1: res = match * res
        else: assert len(res)==match, 'Match length mismatch'
    return res

# %% ../nbs/01_basics.ipynb 34
def tuplify(o, use_list=False, match=None):
    "Make `o` a tuple"
    return tuple(listify(o, use_list=use_list, match=match))

# %% ../nbs/01_basics.ipynb 36
def true(x):
    "Test whether `x` is truthy; collections with >0 elements are considered `True`"
    try: return bool(len(x))
    except: return bool(x)

# %% ../nbs/01_basics.ipynb 38
class NullType:
    "An object that is `False` and can be called, chained, and indexed"
    def __getattr__(self, *args): return null
    def __call__(self, *args, **kwargs): return null
    def __getitem__(self, *args): return null
    def __bool__(self): return False

null = NullType()

# %% ../nbs/01_basics.ipynb 40
def tonull(x):
    "Convert `None` to `null`"
    return null if x is None else x

# %% ../nbs/01_basics.ipynb 42
def get_class(nm, *fld_names, sup=None, doc=None, funcs=None, **flds):
    "Dynamically create a class, optionally inheriting from `sup`, containing `fld_names`"
    attrs = {}
    for f in fld_names: attrs[f] = None
    for f in listify(funcs): attrs[f.__name__] = f
    for k,v in flds.items(): attrs[k] = v
    sup = ifnone(sup,())
    # because type accepts second argument as a tuple
    if not isinstance(sup, tuple): sup = (sup,)
    
    def _init(self, *args, **kwargs):
        # sets attrs for any kwargs, and for any args (matching by position to fields)
        for i,v in enumerate(args): setattr(self, list(attrs.keys())[i], v)
        # additional to get_class kwargs can be passed here
        for k,v in kwargs.items(): setattr(self,k,v)
        
    all_flds = [*fld_names, *flds.keys()]
    
    def _eq(self, b):
        return all([getattr(self,k) == getattr(b, k) for k in all_flds])
    
    if not sup: attrs['__repr__'] = basic_repr(all_flds)
    attrs['__init__'] = _init
    attrs['__eq__'] = _eq
    # res is created as a class with name nm, base class and attrs
    res = type(nm, sup, attrs)
    if doc is not None: res.__doc__ = doc
    return res

# %% ../nbs/01_basics.ipynb 47
def mk_class(nm, *fld_names, sup=None, doc=None, funcs=None, mod=None, **flds):
    "Create a class using `get_class` and add to the caller's module"
    if mod is None: mod = sys._getframe(1).f_locals
    res = get_class(nm, *fld_names, sup=sup, doc=doc, funcs=funcs, **flds)
    mod[nm] = res

# %% ../nbs/01_basics.ipynb 52
def wrap_class(nm, *fld_names, sup=None, doc=None, funcs=None, **flds):
    "Decorator: makes function a method of a new class `nm` passing parameters to `mk_class`"
    def _inner(f):
        mk_class(nm, *fld_names, sup=sup, doc=doc, funcs=listify(funcs)+[f], mod=f.__globals__, **flds)
        return f
    return _inner

# %% ../nbs/01_basics.ipynb 54
class ignore_exceptions:
    "Context manager to ignore exceptions"
    def __enter__(self): pass
    def __exit__(self, *args): 
        return True

# %% ../nbs/01_basics.ipynb 57
def exec_local(code, var_name):
    "Call `exec` on `code` and return the var `var_name`"
    loc = {}
    exec(code, globals(), loc)
    return loc[var_name]

# %% ../nbs/01_basics.ipynb 60
def risinstance(types, obj=None):
    "Curried `isinstance` but with args reversed"
    types = tuplify(types)
    # return partial function that accepts only obj
    if obj is None: return partial(risinstance, types)
    # if obj is of type string, check if name of object type name (or its parent)
    if any(isinstance(t, str) for t in types):
        return any(t.__name__ in types for t in type(obj).__mro__)
    return isinstance(obj, types)

# %% ../nbs/01_basics.ipynb 73
class _InfMeta(type):
    @property
    def count(self): return itertools.count()
    @property
    def zeros(self): return itertools.cycle([0])
    @property
    def ones(self): return itertools.cycle([1])
    @property
    def nones(self): return itertools.cycle([None])

# %% ../nbs/01_basics.ipynb 74
class Inf(metaclass=_InfMeta):
    "Infinite lists"
    pass

# %% ../nbs/01_basics.ipynb 77
_dumobj = object()
# if b is not provided returns lambda function
def _oper(op,a,b=_dumobj): return (lambda o: op(o,a)) if b is _dumobj else op(a,b)

def _mk_op(nm, mod):
    "Create an operator using `_oper` and add to the caller's module"
    # get operator.nm
    op = getattr(operator, nm)
    # internal f-n that will be added to module to be called with one or two args
    def _inner(a, b=_dumobj): return _oper(op,a,b)
    # __qualname__ provides a qualified name for classes and functions
    _inner.__name__ = _inner.__qualname__ = nm
    _inner.__doc__ = f'Same as `operator.{nm}` or returns partial if 1 arg'
    mod[nm] = _inner

# %% ../nbs/01_basics.ipynb 79
def in_(x, a):
    "True if `x in a`"
    return x in a

operator.in_ = in_

# %% ../nbs/01_basics.ipynb 80
_all_ = ['lt','gt','le','ge','eq','ne','add','sub','mul','truediv','is_','is_not','in_', 'mod']

# %% ../nbs/01_basics.ipynb 81
for op in ['lt','gt','le','ge','eq','ne','add','sub','mul','truediv','is_','is_not','in_', 'mod']: _mk_op(op, globals())

# %% ../nbs/01_basics.ipynb 86
def ret_true(*args, **kwargs):
    "Predicate: always `True`"
    return True

# %% ../nbs/01_basics.ipynb 88
def ret_false(*args, **kwargs):
    "Predicate: always `False`"
    return False

# %% ../nbs/01_basics.ipynb 90
def stop(e=StopIteration):
    "Raises exception `e` (by default `StopException`)"
    raise e

# %% ../nbs/01_basics.ipynb 91
def gen(func, seq, cond=ret_true):
    "Like `(func(o) for o in seq if cond(func(o)))` but handles `StopIteration`"
    return itertools.takewhile(cond, map(func,seq))

# %% ../nbs/01_basics.ipynb 93
def chunked(it, chunk_sz=None, drop_last=False, n_chunks=None):
    "Return batches from iterator `it` of size `chunk_sz` (or return `n_chunks` total)"
    # either `chunk_sz` is provided or `n_chunks`, not both
    assert bool(chunk_sz) ^ bool(n_chunks)
    if n_chunks: chunk_sz = max(math.ceil(len(it) / n_chunks), 1)
    if not isinstance(it, Iterator): it = iter(it)
    while True:
        res = list(itertools.islice(it, chunk_sz))
        if res and (len(res) == chunk_sz or not drop_last): yield res
        if len(res) < chunk_sz: return

# %% ../nbs/01_basics.ipynb 96
def otherwise(x, tst, y):
    "`y if tst(x) else x`"
    return y if tst(x) else x

# %% ../nbs/01_basics.ipynb 100
def custom_dir(c, add):
    "Implement custom `__dir__`, adding `add` to `cls`"
    return object.__dir__(c) + listify(add)

# %% ../nbs/01_basics.ipynb 103
class AttrDict(dict):
    "`dict` subclass that also provides access to keys as attrs"
    def __getattr__(self, k): return self[k] if k in self.keys() else stop(AttributeError(k))
    # choose what method to use based on the key (if it starts with _ or not)
    def __setattr__(self, k, v): (self.__setitem__, super().__setattr__)[k[0]=='_'](k,v)
    def __dir__(self): return super().__dir__() + list(self.keys())
    # to display in Jupyter Notebook
    def _repr_markdown_(self): return f'```json\n{pprint.pformat(self, indent=2)}\n```'

# %% ../nbs/01_basics.ipynb 109
class NS(SimpleNamespace):
    "`SimpleNamespace` subclass that also adds `iter` and `dict` support"
    def __iter__(self): return iter(self.__dict__)
    def __getitem__(self, x): return self.__dict__[x]
    def __setitem__(self, x, y): self.__dict__[x] = y

# %% ../nbs/01_basics.ipynb 117
def partition(coll, f):
    "Partition a collection by a predicate"
    # truthes and falses
    ts, fs = [], []
    for o in coll: (fs, ts)[f(o)].append(o)
    if isinstance(coll, tuple):
        typ = type(coll)
        ts, fs = typ(ts), typ(fs)
    return ts, fs

# %% ../nbs/01_basics.ipynb 119
def flatten(o):
    "Concatenate all collections and items as a generator"
    for item in o:
        if isinstance(item, str): yield item; continue
        try: yield from flatten(item)
        except TypeError: yield item

# %% ../nbs/01_basics.ipynb 121
def concat(colls)->list:
    "Concatenate all collections and items as a list"
    return list(flatten(colls))

# %% ../nbs/01_basics.ipynb 124
def strcat(its, sep:str='')->str:
    "Concatenate stringified items `its`"
    return sep.join(map(str,its))

# %% ../nbs/01_basics.ipynb 126
def detuplify(x):
    "If `x` is a tuple with one thing, extract it"
    return None if len(x)==0 else x[0] if len(x)==1 and getattr(x, 'ndim', 1)==1 else x

# %% ../nbs/01_basics.ipynb 128
def replicate(item, match):
    "Create tuple of `item` copied `len(match)` times"
    return (item,) * len(match)

# %% ../nbs/01_basics.ipynb 130
def setify(o):
    "Turn any list like-object into a set."
    return o if isinstance(o, set) else set(listify(o))

# %% ../nbs/01_basics.ipynb 132
def merge(*ds):
    "Merge all dictionaries in `ds`"
    return {k:v for d in ds if d is not None for k,v in d.items()}

# %% ../nbs/01_basics.ipynb 134
def range_of(x):
    "All indices of collection `x` (i.e. `list(range(len(x)))`)"
    return list(range(len(x)))

# %% ../nbs/01_basics.ipynb 138
def groupby(x, key, val=noop):
    "Like `itertools.groupby` but doesn't need to be sorted, and isn't lazy, plus some extensions. x is iterable"
    if   isinstance(key, int): key = itemgetter(key)
    elif isinstance(key, str): key = attrgetter(key)
    if   isinstance(val, int): val = itemgetter(val)
    elif isinstance(val, str): val = attrgetter(val)
    res = {}
    # setdefault return default ([]) if there is no key. Else returns value
    for o in x: res.setdefault(key(o), []).append(val(o))
    return res

# %% ../nbs/01_basics.ipynb 143
def last_index(x, o):
    "Finds the last index of occurence of `x` in `o` (returns -1 if no occurence)"
    try: return next(i for i in reversed(range(len(o))) if o[i] == x)
    except StopIteration: return -1

# %% ../nbs/01_basics.ipynb 145
def filter_dict(d, func):
    "Filter a `dict` using `func`, applied to keys and values"
    return {k:v for k,v in d.items() if func(k,v)}

# %% ../nbs/01_basics.ipynb 148
def filter_keys(d, func):
    "Filter a `dict` using `func`, applied to keys"
    return {k:v for k,v in d.items() if func(k)}

# %% ../nbs/01_basics.ipynb 150
def filter_values(d, func):
    "Filter a `dict` using `func`, applied to values"
    return {k:v for k,v in d.items() if func(v)}

# %% ../nbs/01_basics.ipynb 152
def cycle(o):
    "Like `itertools.cycle` except creates list of `None`s if `o` is empty"
    o = listify(o)
    return itertools.cycle(o) if o is not None and len(o) > 0 else itertools.cycle([None])

# %% ../nbs/01_basics.ipynb 154
def zip_cycle(x, *args):
    "Like `itertools.zip_longest` but `cycle`s through elements of all but first argument"
    return zip(x, *map(itertools.cycle,args))

# %% ../nbs/01_basics.ipynb 158
def sorted_ex(iterable, key=None, reverse=False):
    "Like `sorted`, but if key is str use `attrgetter`; if int use `itemgetter`"
    if isinstance(key, str): k = lambda o: getattr(o,k,0)
    if isinstance(key, int): k = itemgetter(key)
    else: k=key
    return sorted(iterable, key=k, reverse=reverse)

# %% ../nbs/01_basics.ipynb 159
def not_(f):
    "Create new function that negates result of `f`"
    def _f(*args, **kwargs): return not f(*args, **kwargs)
    return  _f

# %% ../nbs/01_basics.ipynb 161
def argwhere(iterable, f, negate=False, **kwargs):
    "Like `filter_ex`, but return indices for matching items"
    if kwargs: f = partial(f, **kwargs)
    if negate: f = not_(f)
    return [i for i,o in enumerate(iterable) if f(o)]

# %% ../nbs/01_basics.ipynb 162
def filter_ex(iterable, f=noop, negate=False, gen=False, **kwargs):
    "Like `filter`, but passing `kwargs` to `f`, defaulting `f` to `noop`, and adding `negate` and `gen`"
    if f is None: f = lambda _: True
    if kwargs: f = partial(f, **kwargs)
    if negate: f = not_(f)
    res = filter(f, iterable)
    if gen: return res
    return list(res)

# %% ../nbs/01_basics.ipynb 164
def range_of(a, b=None, step=None):
    "All indices of collection `a`, if `a` is a collection, otherwise `range`"
    if is_coll(a): a = len(a)
    return list(range(a, b, step) if step is not None else range(a,b) if b is not None else range(a))

# %% ../nbs/01_basics.ipynb 166
def renumerate(iterable, start=0):
    "Same as `enumerate`, but returns index as 2nd element instead of 1st"
    return ((o,i) for i,o in enumerate(iterable, start=start))

# %% ../nbs/01_basics.ipynb 168
def only(o):
    "Return the only item of `o`, raise if `o` doesn't have exactly one item"
    it = iter(o)
    try: res = next(it)
    except StopIteration: raise ValueError('iterable has 0 items') from None
    try: next(it)
    except StopIteration: return res
    raise ValueError('iterable has more than 1 item')
