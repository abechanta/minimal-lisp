# todo list:
# + introduce new type addr for flexible addressing by car/cdr/elt with setf
# + implement nil as symbol, not None in python
# + not eval list by default
# + not eval last element at dot list by default
# + support (= 'a 'a) as t
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
        return t('eval', 'value not defined yet.')


class nil(atom):
    def parse(s: str) -> t:
        if s == 'nil':
            return nil()
        return None

    def __init__(self):
        pass

    def __str__(self) -> str:
        return 'nil'

    def eval(self) -> t:
        return self


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


class cons(t):
    def __init__(self, car: t, cdr: t = None):
        self.car = car if car else nil()
        self.cdr = None if isinstance(cdr, nil) else cdr

    def __str__(self) -> str:
        s = '('
        s += str(self.car) if self.car else 'nil'
        cdr = self.cdr
        while cdr != None:
            if isinstance(cdr, cons):
                s += ' ' + str(cdr.car)
                cdr = cdr.cdr
            else:
                s += ' . ' + str(cdr)
                cdr = None
        s += ')'
        return s

    def eval(self) -> t:
        car = self.car.eval() if isinstance(self.car, symbol) else self.car
        if t.iserr(car):
            return car
        if isinstance(car, function):
            if t.iserr(self.cdr):
                return self.cdr
            return car.eval(self.cdr) if not self.cdr or isinstance(self.cdr, cons) else t('call')
        return self


class symbol(t):
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
        self.key = key

    def __str__(self) -> str:
        return self.key

    def assign(self, val: t) -> t:
        if symbol.local:
            table = symbol.scope[-1]
        else:
            table = *filter(lambda tbl: self.key in tbl, reversed(symbol.scope)),
            table = table[0] if len(table) else symbol.scope[0]
        if val:
            table[self.key] = val
            return val
        if self.key in table:
            del table[self.key]
        return nil()

    def eval(self) -> t:
        for table in reversed(symbol.scope):
            if self.key in table:
                return table[self.key]
        return t('symbol', self.key)


#
# repl
#

def parse_tokens(tok: [str]) -> t:
    if not tok:
        return None, tok
    x = nil.parse(tok[0])
    if x:
        return x, tok[1:]
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
            return nil(), tok[1:]
        while tok[0] != ')':
            x, tok = parse_tokens(tok)
            if not x:
                return None, tok
            lst.append(x)
        x = None
        while len(lst) > 0:
            x = cons(lst.pop(), x)
        return x, tok[1:]
    return None, tok

def parse_line(s: str) -> t:
    tok = s.replace('(', '( ').replace(')', ' )').replace("'", "' ").split()
    x, tok = parse_tokens(tok)
    if not x:
        return t('parse', 'unmatched braces')            
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
# system values
#

tv = symbol('t')
tv.assign(tv)

#
# system functions
#

def _print(x: t) -> t:
    if not isinstance(x, cons):
        return t('arg', 'print')
    v = x.car.eval()
    print(v)
    return v

symbol('print').assign(function(_print))

#symbol('readline').assign(function(_readline))

def _setq(x: t) -> t:
    if not x or isinstance(x, nil):
        return nil()
    if not isinstance(x, cons) or not isinstance(x.car, symbol) or not isinstance(x.cdr, cons):
        return t('arg', 'setq')
    cdr = x.cdr.car.eval()
    if t.iserr(cdr):
        return cdr
    v = x.car.assign(cdr)
    cdr2 = _setq(x.cdr.cdr)
    if t.iserr(cdr2):
        return cdr2
    return cons(v, cdr2)

symbol('setq').assign(function(_setq))

def _setf(x: t) -> t:
    if not x or isinstance(x, nil):
        return nil()
    if not isinstance(x, cons) or not isinstance(x.car, (symbol, cons)) or not isinstance(x.cdr, cons):
        return t('arg', 'setf')
    if isinstance(x.car, symbol):
        cdr = x.cdr.car.eval()
        if t.iserr(cdr):
            return cdr
        v = x.car.assign(cdr)
    if isinstance(x.car, cons):
        adr = x.car.eval()
        if t.iserr(adr):
            return cdr
        v = x.cdr.car
        adr.car = v
    cdr2 = _setf(x.cdr.cdr)
    if t.iserr(cdr2):
        return cdr2
    return cons(v, cdr2)

symbol('setf').assign(function(_setf))

symbol('quote').assign(function(lambda x:
    x.car if isinstance(x, cons) else nil()
))

symbol('eval').assign(function(lambda x:
    x.car.eval().eval() if isinstance(x, cons) else nil()
))

def _list(x: t) -> t:
    if not x:
        return nil()
    if not isinstance(x, cons):
        return t('arg', 'list')
    rv = symbol("'return")
    rv.assign(None)
    car = x.car.eval()
    if t.iserr(car):
        return car
    if not t.iserr(rv.eval()):
        return cons(rv.eval())
    cdr = _list(x.cdr)
    if t.iserr(cdr):
        return cdr
    return cons(car, cdr)

symbol('list').assign(function(_list))

def _car(x: t) -> t:
    if not isinstance(x, cons) or not isinstance(x.car, (cons, symbol)):
        return nil()
    return x.car.eval()

symbol('car').assign(function(_car))

def _cdr(x: t) -> t:
    if not isinstance(x, cons) or not isinstance(x.car, (cons, symbol)):
        return nil()
    x = x.car.eval()
    if t.iserr(x):
        return x
    return x.cdr if isinstance(x.cdr, cons) else nil()

symbol('cdr').assign(function(_cdr))

def _cons(x: t) -> t:
    if not isinstance(x, cons):
        return t('arg', 'cons')
    car = x.car.eval()
    if t.iserr(car):
        return car
    cdr = x.cdr.car.eval() if isinstance(x.cdr, cons) else x.cdr.eval()
    if t.iserr(cdr):
        return cdr
    return cons(car, cdr)

symbol('cons').assign(function(_cons))

#symbol('append').assign(function(_append))

def _if(x: t) -> t:
    if not isinstance(x, cons) or not isinstance(x.cdr, cons):
        return t('arg', 'if')
    car = x.car.eval()
    if t.iserr(car):
        return car
    if not isinstance(car, nil):
        v = x.cdr.car.eval()
    else:
        v = x.cdr.cdr.car.eval() if isinstance(x.cdr.cdr, cons) else nil()
    symbol("'condition").assign(car)
    return v

symbol('if').assign(function(_if))

def _cond(x: t) -> t:
    if not isinstance(x, cons) or not isinstance(x.cdr, cons):
        return t('arg', 'cond')
    rv = symbol("'condition")
    v = nil()
    while x:
        rv.assign(None)
        v = _if(x.car)
        if t.iserr(v) or not isinstance(rv.eval(), nil):
            break
        x = x.cdr
    return v

symbol('cond').assign(function(_cond))

def _loop(x: t) -> t:
    if not isinstance(x, cons) or not isinstance(x.cdr, cons):
        return t('arg', 'loop')
    rv = symbol("'return")
    v = nil()
    while True:
        car = x.car.eval()
        if t.iserr(car):
            return car
        if isinstance(car, nil):
            break
        rv.assign(None)
        v = _list(x.cdr)
        if t.iserr(v):
            return v
        if not t.iserr(rv.eval()):
            return rv.eval()
    return nil()

symbol('loop').assign(function(_loop))

def _return(x: t) -> t:
    if not isinstance(x, cons):
        return t('arg', 'return')
    v = x.car.eval()
    if t.iserr(v):
        return v
    rv = symbol("'return")
    return rv.assign(v)

symbol('return').assign(function(_return))

def _let(x: t) -> t:
    if not isinstance(x, cons) or not isinstance(x.car, cons) or not isinstance(x.cdr, cons):
        t('arg', 'let')
    v = symbol.push(lambda: _setq(x.car))
    if t.iserr(v):
        return symbol.pop(lambda: v)
    v = _list(x.cdr)
    if t.iserr(v) or not isinstance(v, cons):
        return symbol.pop(lambda: v)
    while v.cdr:
        v = v.cdr
    return symbol.pop(lambda: v.car)

symbol('let').assign(function(_let))

def _is_symbol(x: t) -> bool:
    if not x:
        return True
    if not isinstance(x.car, symbol):
        return False
    return _is_symbol(x.cdr)

def _merge(x: t, y: t) -> t:
    if not x or not y:
        return nil() if not x and not y else t('arg', 'merge')
    return cons(x.car, cons(y.car, _merge(x.cdr, y.cdr)))

def _lambda(x: t, y: t):
    return lambda z: _let(cons(_merge(x, _list(z)), cons(y)))

def _defun(x: t) -> t:
    if not x or not isinstance(x, cons) or not isinstance(x.car, symbol) or not isinstance(x.cdr, cons) or not isinstance(x.cdr.car, cons) or not isinstance(x.cdr.cdr, cons) or not _is_symbol(x.cdr.car):
        return t('arg', 'defun')
    return x.car.assign(function(_lambda(x.cdr.car, x.cdr.cdr.car)))

symbol('defun').assign(function(_defun))

#
# math functions
#

def _reduce_l(f, y: t, x: t) -> t:
    if not x:
        return y
    car = x.car.eval() if isinstance(x, cons) else x.eval()
    if not t.iserr(car) and not isinstance(x.cdr, atom):
        cdr = _reduce_l(f, y, x.cdr)
        if t.iserr(cdr):
            return cdr
        return number(f(car.val, cdr.val))
    return car

def _add(x: t) -> t:
    return _reduce_l(lambda x, y: x + y, number(0), x)

symbol('+').assign(function(_add))

def _mul(x: t) -> t:
    return _reduce_l(lambda x, y: x * y, number(1), x)

symbol('*').assign(function(_mul))

def _sub(x: t) -> t:
    if not x:
        return t('arg', 'sub')
    car = x.car.eval() if isinstance(x, cons) else x.eval()
    if t.iserr(car):
        return car
    if isinstance(x, cons) and x.cdr:
        cdr = _reduce_l(lambda x, y: x + y, number(0), x.cdr)
        if t.iserr(cdr):
            return cdr
        return number(car.val - cdr.val)
    return number(-car.val)

symbol('-').assign(function(_sub))

def _div(x: t) -> t:
    if not x:
        return t('arg', 'div')
    car = x.car.eval() if isinstance(x, cons) else x.eval()
    if t.iserr(car):
        return car
    if isinstance(x, cons) and x.cdr:
        cdr = _reduce_l(lambda x, y: x * y, number(1), x.cdr)
        if t.iserr(cdr):
            return cdr
        if cdr.val == 0:
            return t('division', 'div')
        return number(car.val / cdr.val)
    if car.val == 0:
        return t('division', 'div')
    return number(1 / car.val)

symbol('/').assign(function(_div))

#
# pred functions
#

def _iterate_l(f, x: t) -> t:
    if not x:
        return tv
    car = x.car.eval() if isinstance(x, cons) else x.eval()
    if t.iserr(car):
        return car
    if f(car):
        return _iterate_l(f, x.cdr)
    return nil()

symbol('not').assign(function(lambda x:
    tv if isinstance(x, cons) and isinstance(x.car, nil) or isinstance(x, nil) else nil()
))

symbol('and').assign(function(lambda x:
    _iterate_l(lambda x: not isinstance(x, nil), x)
))

symbol('or').assign(function(lambda x:
    tv if not x or isinstance(_iterate_l(lambda x: isinstance(x, nil), x), nil) else nil()
))

def _adjacent_l(f, y: t, x: t) -> t:
    if not x:
        return tv
    car = x.car.eval() if isinstance(x, cons) else x.eval()
    if t.iserr(car):
        return car
    if not y or f(y, car):
        return _adjacent_l(f, car, x.cdr)
    return nil()

symbol('=').assign(function(lambda x:
    # fixme: (= 'a 'a) ===> error
    _adjacent_l(lambda x, y: x.val == y.val, None, x)
))

symbol('/=').assign(function(lambda x:
    _adjacent_l(lambda x, y: x.val != y.val, None, x)
))

symbol('<').assign(function(lambda x:
    _adjacent_l(lambda x, y: x.val < y.val, None, x)
))

symbol('<=').assign(function(lambda x:
    _adjacent_l(lambda x, y: x.val <= y.val, None, x)
))

symbol('>').assign(function(lambda x:
    _adjacent_l(lambda x, y: x.val > y.val, None, x)
))

symbol('>=').assign(function(lambda x:
    _adjacent_l(lambda x, y: x.val >= y.val, None, x)
))

if __name__ == '__main__':
    print('(defun fact (x) (if (<= x 1) 1 (* x (fact (- x 1)))))', '===>', 'lambda')
    print('(let (x 1) (loop (< x 10) (print (fact x)) (setq x (+ x 1))))', '===>', '362880')
    repl()

