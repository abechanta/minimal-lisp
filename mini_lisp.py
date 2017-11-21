# todo list:
# + support parsing list of words
# + support for fraction


#
# types
#

class t:
    def __init__(self, category: str, message: str = ''):
        self.category = category
        self.message = message

    def __str__(self) -> str:
        return self.category + ' error: ' + self.message

    def eval(self):
        print(self)
        return self

    def iserr(x) -> bool:
        return type(x) == t


class atom(t):
    def __init__(self):
        pass

    def eval(self) -> t:
        return t('eval', 'value not defined yet')


class number(atom):
    def parse(s: str) -> t:
        if s.isnumeric() or s[0] in '+-' and s[1:].isnumeric():
            return number(int(s))
        # todo: support for fraction
        return None

    def __init__(self, val: int):
        self.val = val

    def __str__(self) -> str:
        return str(self.val)

    def eval(self) -> atom:
        return self


class string(atom):
    def parse(s: str) -> t:
        if len(s) >= 2 and s.startswith('"') and s.endswith('"'):
            return string(s[1:-1])
        # todo: support list of words
        return None

    def __init__(self, val: str):
        self.val = val

    def __str__(self) -> str:
        return '"' + self.val + '"'

    def eval(self) -> atom:
        return self


class function(atom):
    def __init__(self, proc):
        self.proc = proc

    def __str__(self) -> str:
        return 'lambda'

    def eval(self, arg: t) -> t:
        return self.proc(arg)


class symbol(atom):
    scope = [{}]
    local = False

    def push(f = lambda: None):
        symbol.scope.append({})
        symbol.local = True
        fv = f()
        symbol.local = False
        return fv

    def pop(f = lambda: None):
        fv = f()
        symbol.scope.pop()
        return fv

    def parse(s: str) -> t:
        if not '(' in s and not ')' in s and not '"' in s and not "'" in s and not ':' in s and not '\\' in s and s.isprintable():
            return symbol(s)
        return None

    def __init__(self, key: str):
        self.val = key

    def __str__(self) -> str:
        return self.val

    def assign(self, val: t) -> t:
        if symbol.local:
            table = symbol.scope[-1]
        else:
            table = *filter(lambda tbl: self.val in tbl, reversed(symbol.scope)),
            table = table[0] if len(table) else symbol.scope[0]
        if val:
            table[self.val] = val
            return val
        if self.val in table:
            del table[self.val]
        return symbol('nil')

    def eval(self) -> t:
        for table in reversed(symbol.scope):
            if self.val in table:
                return table[self.val]
        return t('symbol', self.val)

nv = symbol('nil')
nv.assign(nv)    # system values
tv = symbol('t')
tv.assign(tv)    # system values


class cons(t):
    def __init__(self, car: t, cdr: t = nv):
        self.car = car if car else nv
        self.cdr = cdr if cdr else nv

    def __str__(self) -> str:
        s = '('
        s += str(self.car)
        cdr = self.cdr
        while cdr != nv:
            if isinstance(cdr, cons):
                s += ' ' + str(cdr.car)
                cdr = cdr.cdr
            else:
                s += ' . ' + str(cdr)
                cdr = nv
        s += ')'
        return s

    def eval(self) -> t:
        if not isinstance(self.car, (symbol, cons)):
            return t('eval', 'no function')
        car = self.car.eval()
        if t.iserr(car):
            return car
        if not isinstance(car, function):
            return t('eval', 'no function')
        return car.eval(self.cdr)


#
# repl
#

def parse_tokens(tok: [str]) -> t:
    if not tok:
        return None, tok
    x = number.parse(tok[0])
    if x:
        return x, tok[1:]
    x = string.parse(tok[0])
    if x:
        return x, tok[1:]
    x = symbol.parse(tok[0])
    if x:
        return x, tok[1:]
    if tok[0] == "'":
        x, tok = parse_tokens(tok[1:])
        if not x:
            return None, tok
        return cons(symbol('quote'), cons(x)), tok
    if tok[0] == '(' and len(tok) >= 2:
        lst = []
        tok = tok[1:]
        if tok[0] == ')':
            return nv, tok[1:]
        while tok[0] != ')':
            x, tok = parse_tokens(tok)
            if not x:
                return None, tok
            lst.append(x)
        x = nv
        while len(lst) > 0:
            x = cons(lst.pop(), x)
        return x, tok[1:]
    return None, tok


def parse_line(s: str) -> t:
    tok = s.replace('(', '( ').replace(')', ' )').replace("'", "' ").split()
    x, tok = parse_tokens(tok)
    if not x:
        return t('parse', 'unmatched brackets')            
    if tok:
        return t('parse', str(tok))
    return x


def read() -> t:
    while True:
        l = input(':> ')
        if not l:
            continue
        if l == 'q':
            return None
        x = parse_line(l)
        if not x:
            continue
        break
    return x


def eval(x: t) -> t:
    return x.eval()


def repl():
    print('''
minimal lisp started!
type "q" to exit.''')
    while True:
        x = read()
        if not x:
            break
        s = eval(x)
        print('===>', s)


#
# system functions
#

def _exec(l: []) -> t:
    a = {}
    for f in l:
        k, v = f(a)
        if t.iserr(v) and k[0] not in ('+-') or not t.iserr(v) and k[0] in '+':
            break
        a[k] = v
    return v


def _elem_nth(x: t, nth: int, type, message: str) -> t:
    if isinstance(x, cons):
        return x.car if nth <= 0 and isinstance(x.car, type) else _elem_nth(x.cdr, nth - 1, type, message)
    return t('arg', message)


def _eval_nth(x: t, nth: int, message: str) -> t:
    s = _elem_nth(x, nth, (atom, cons), message)
    return s if t.iserr(s) else s.eval()


def _print(x: t) -> t:
    return _exec([
        lambda a: ('v0', _eval_nth(x, 0, _print.__name__)),
        lambda a: ('t0', print(a.get('v0'))),
        lambda a: ('rv', a.get('v0')),
    ])

symbol('print').assign(function(_print))


def _readline(x: t) -> t:
    return _exec([
        lambda a: ('-v0', _eval_nth(x, 0, _readline.__name__)),
        lambda a: ('v0', '' if t.iserr(a.get('-v0')) else a.get('-v0')),
        lambda a: ('rv', string(input(a.get('v0')))),
    ])

symbol('readline').assign(function(_readline))


def _setq(x: t) -> t:
    return _exec([
        lambda a: ('e0', _elem_nth(x, 0, symbol, _setq.__name__)),
        lambda a: ('v1', _eval_nth(x, 1, _setq.__name__)),
        lambda a: ('t0', a.get('e0').assign(a.get('v1'))),
        lambda a: ('rv', a.get('t0') if x.cdr.cdr == nv else _setq(x.cdr.cdr)),
    ])

symbol('setq').assign(function(_setq))


def _setf(x: t) -> t:
    return _exec([
        lambda a: ('-e0', _elem_nth(x, 0, symbol, _setf.__name__)),
        lambda a: ('v0', _eval_nth(x, 0, _setf.__name__) if t.iserr(a.get('-e0')) else a.get('-e0')),
        lambda a: ('v0', a.get('v0') if a.get('v0') != nv else t('eval', 'not addressed')),
        lambda a: ('v1', _eval_nth(x, 1, _setf.__name__)),
        lambda a: ('t0', a.get('v0').assign(a.get('v1'))),
        lambda a: ('rv', a.get('t0') if x.cdr.cdr == nv else _setf(x.cdr.cdr)),
    ])

symbol('setf').assign(function(_setf))


symbol('quote').assign(function(lambda x:
    _elem_nth(x, 0, t, '_quote')
))


def _eval(x: t) -> t:
    return _exec([
        lambda a: ('v0', _eval_nth(x, 0, _eval.__name__)),
        lambda a: ('rv', a.get('v0').eval()),
    ])

symbol('eval').assign(function(_eval))


def _addr(x: t, idx: t) -> t:
    def _add_assign(x: t, idx: int) -> t:
        def _assign_car(val: t) -> t:
            x.car = val
            return val
        def _assign_cdr(val: t) -> t:
            x.cdr = val
            return val
        if not isinstance(x, cons):
            return nv
        if idx < 0:
            x.cdr.assign = _assign_cdr
            return x.cdr
        if idx == 0:
            x.car.assign = _assign_car
            return x.car
        return _add_assign(x.cdr, idx - 1)
    return _exec([
        lambda a: ('v0', _eval_nth(x, 0, _addr.__name__)),
        lambda a: ('idx', _eval_nth(x, 1, _addr.__name__) if idx == nv else idx),
        lambda a: ('rv', _add_assign(a.get('v0'), a.get('idx').val) if isinstance(a.get('idx'), number) and a.get('idx').val >= -1 else nv),
    ])

symbol('car').assign(function(lambda x:
    _addr(x, number(0))
))
symbol('cdr').assign(function(lambda x:
    _addr(x, number(-1))
))
symbol('elt').assign(function(lambda x:
    _addr(x, nv)
))


def _cons(x: t) -> t:
    return _exec([
        lambda a: ('v0', _eval_nth(x, 0, _cons.__name__)),
        lambda a: ('v1', _eval_nth(x, 1, _cons.__name__)),
        lambda a: ('rv', cons(a.get('v0'), a.get('v1'))),
    ])

symbol('cons').assign(function(_cons))


def _progn(x: t) -> t:
    return _exec([
        lambda a: ('v0', _eval_nth(x, 0, _progn.__name__)),
        lambda a: ('rv', a.get('v0') if x.cdr == nv else _progn(x.cdr)),
    ])

symbol('progn').assign(function(_progn))


def _list(x: t) -> t:
    return _exec([
        lambda a: ('v0', _eval_nth(x, 0, _list.__name__)),
        lambda a: ('v1', nv if x.cdr == nv else _list(x.cdr)),
        lambda a: ('rv', cons(a.get('v0'), a.get('v1'))),
    ])

symbol('list').assign(function(_list))


def _if(x: t, out = {}) -> t:
    def _set_out(k, v):
        out[k] = v
        return v
    return _exec([
        lambda a: ('b0', _set_out('predicate', _eval_nth(x, 0, _if.__name__))),
        lambda a: ('-e2', _elem_nth(x, 2, t, _if.__name__)),
        lambda a: ('rv', _eval_nth(x, 1, _if.__name__) if a.get('b0') != nv else _eval_nth(x, 2, _if.__name__) if not t.iserr(a.get('-e2')) else nv),
    ])

symbol('if').assign(function(_if))


def _cond(x: t) -> t:
    rv = {}
    return _exec([
        lambda a: ('e0', _elem_nth(x, 0, cons, _cond.__name__)),
        lambda a: ('e0', _if(a.get('e0'), rv)),
        lambda a: ('rv', a.get('e0') if rv.get('predicate') != nv else _cond(x.cdr) if isinstance(x.cdr, cons) else nv),
    ])

symbol('cond').assign(function(_cond))


def _while(x: t) -> t:
    v, rx, rv = nv, symbol("'return"), {'predicate': tv, }
    symbol.push(lambda: rx.assign(cons(nv, nv)))
    while rv.get('predicate') != nv and rx.eval().cdr == nv:
        v = _if(x, rv)
        if t.iserr(v):
            break
        if rx.eval().cdr != nv:
            v = rx.eval().car
            break
    return symbol.pop(lambda: v)

symbol('while').assign(function(_while))


def _return(x: t) -> t:
    return _exec([
        lambda a: ('v0', _eval_nth(x, 0, _return.__name__)),
        lambda a: ('t0', symbol("'return").assign(cons(a.get('v0'), tv))),
        lambda a: ('rv', a.get('v0')),
    ])

symbol('return').assign(function(_return))


def _let(x: t) -> t:
    return symbol.pop(lambda: _exec([
        lambda a: ('-e0', _elem_nth(x, 0, (cons, symbol), _let.__name__)),
        lambda a: ('t0', symbol.push(lambda: _setq(a.get('-e0')) if not t.iserr(a.get('-e0')) and a.get('-e0') != nv else a.get('-e0'))),
        lambda a: ('e1', _elem_nth(x, 1, t, _let.__name__)),
        lambda a: ('rv', _progn(x.cdr)),
    ]))

symbol('let').assign(function(_let))


def _is_symbol(x: t) -> t:
    if x == nv:
        return tv
    if not isinstance(x.car, symbol):
        return nv
    return _is_symbol(x.cdr)


def _merge(x: t, y: t) -> t:
    if x == nv or y == nv:
        return nv if x == nv and y == nv else t('call', merge.__name__)
    return cons(x.car, cons(y.car, _merge(x.cdr, y.cdr)))


def _lambda(x: t, y: t) -> t:
    return lambda z: _let(cons(_merge(x, z), cons(y)))


def _defun(x: t) -> t:
    return _exec([
        lambda a: ('e0', _elem_nth(x, 0, symbol, _defun.__name__)),
        lambda a: ('e1', _elem_nth(x, 1, cons, _defun.__name__)),
        lambda a: ('t0', tv if _is_symbol(x.cdr.car) else t('call', 'args')),
        lambda a: ('e2', _elem_nth(x, 2, t, _defun.__name__)),
        lambda a: ('rv', a.get('e0').assign(function(_lambda(a.get('e1'), a.get('e2'))))),
    ])

symbol('defun').assign(function(_defun))


#
# math functions
#

def _reduce_l(f, y: t, x: t) -> t:
    if x == nv:
        return y
    return _exec([
        lambda a: ('v0', _eval_nth(x, 0, _reduce_l.__name__)),
        lambda a: ('t0', number(f(y.val, a.get('v0').val))),
        lambda a: ('rv', _reduce_l(f, a.get('t0'), x.cdr) if x.cdr else a.get('t0')),
    ])

symbol('+').assign(function(lambda x:
    return _reduce_l(lambda x, y: x + y, number(0), x)
))
symbol('*').assign(function(lambda x:
    return _reduce_l(lambda x, y: x * y, number(1), x)
))


def _reduce_l2(f, y: t, x: t) -> t:
    return _exec([
        lambda a: ('v0', _eval_nth(x, 0, _reduce_l2.__name__)),
        lambda a: ('-e1', _elem_nth(x, 1, t, _reduce_l2.__name__)),
        lambda a: ('rv', f(y.val, a.get('v0').val) if t.iserr(a.get('-e1')) else _reduce_l(f, a.get('v0'), x.cdr)),
    ])


symbol('-').assign(function(lambda x:
    _reduce_l2(lambda x, y: x - y, number(0), x)
))
symbol('/').assign(function(lambda x:
    _reduce_l2(lambda x, y: x / y if y != 0 else t('math', 'zero division'), number(1), x)
))


#
# pred functions
#

def _typep_e0(x: t) -> t:
    return _eval_nth(x, 0, _typep_e0.__name__)


symbol('atomp').assign(function(lambda x:
    tv if isinstance(_typep_e0(x), atom) else nv
))
symbol('numberp').assign(function(lambda x:
    tv if isinstance(_typep_e0(x), number) else nv
))
symbol('stringp').assign(function(lambda x:
    tv if isinstance(_typep_e0(x), string) else nv
))
symbol('symbolp').assign(function(lambda x:
    tv if isinstance(_typep_e0(x), symbol) else nv
))
symbol('consp').assign(function(lambda x:
    tv if isinstance(_typep_e0(x), cons) else nv
))


def _not(x: t) -> t:
    return _exec([
        lambda a: ('v0', _eval_nth(x, 0, _not.__name__)),
        lambda a: ('rv', nv if a.get('v0') == nv else tv),
    ])

symbol('not').assign(function(_not))


def _all_of(f, x: t) -> t:
    return _exec([
        lambda a: ('v0', _eval_nth(x, 0, _all_of.__name__)),
        lambda a: ('rv', nv if not f(a.get('v0')) else _all_of(f, x.cdr) if x.cdr != nv else tv),
    ])


def _any_of(f, x: t) -> t:
    return _exec([
        lambda a: ('v0', _eval_nth(x, 0, _any_of.__name__)),
        lambda a: ('rv', tv if f(a.get('v0')) else _any_of(f, x.cdr) if x.cdr != nv else nv),
    ])


symbol('and').assign(function(lambda x:
    _all_of(lambda x: x != nv, x)
))
symbol('or').assign(function(lambda x:
    _any_of(lambda x: x != nv, x)
))


def _adjacent_l(f, y: t, x: t) -> t:
    return _exec([
        lambda a: ('v0', _eval_nth(x, 0, _adjacent_l.__name__)),
        lambda a: ('rv', nv if y and not f(y, a.get('v0')) else _adjacent_l(f, a.get('v0'), x.cdr) if x.cdr != nv else tv),
    ])


symbol('=').assign(function(lambda x:
    _adjacent_l(lambda x, y: x.val == y.val, None, x)
))
symbol('!=').assign(function(lambda x:
    _adjacent_l(lambda x, y: x.val != y.val, None, x)
))
symbol('<').assign(function(lambda x:
    _adjacent_l(lambda x, y: x.val < y.val, None, x)
))
symbol('<=').assign(function(lambda x:
    _adjacent_l(lambda x, y: x.val <= y.val, None, x)
))


if __name__ == '__main__':
    print('(defun append (x y) (if (atomp x) y (cons (car x) (append (cdr x) y))))', '\n', '===>', 'lambda')
    print('(append \'(1 2 3) \'(4 5))', '\n', '===>', '(1 2 3 4 5)')
    print('(defun fact (x) (if (<= x 1) 1 (* x (fact (- x 1)))))', '\n', '===>', 'lambda')
    print('(let (x 1) (while (< x 8) (progn (print (fact x)) (setq x (+ x 1)))))', '\n', '===>', '5040')
    repl()

