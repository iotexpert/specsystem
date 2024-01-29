from django.db.models import Lookup
from django.db.models.fields import Field

@Field.register_lookup
class Like(Lookup):
    lookup_name = 'like'

    def as_sql(self, compiler, connection):
        lhs, lhs_params = self.process_lhs(compiler, connection)
        rhs, rhs_params = self.process_rhs(compiler, connection)
        params = lhs_params + rhs_params
        return '%s LIKE %s' % (lhs, rhs), params

def qsFilter(queryset, request_GET, cols, orderBy = []):
    """
    Filters a queryset based on the input request.
    cols: Array of column names to check request for filter conditions
          entry may be a dictionary: {'f':"<field name>", 't': str|bool, 'e': "filter expression"}
          If a dictionary is passed, f is required.
          t defaults to str
          e defaults to <field>__like
    orderBy: default sort field(s)
    """
    for col in cols:
        if isinstance(col, dict):
            # Default type (t) is str
            # Default match expression (e) is the field (f) __like
            c = {'t':str, } | {'e':'{0}__like'.format(col['f'])} | col
        else:
            c = {'f':col, 't':str, 'e':'{0}__like'.format(col)}

        c_val = request_GET.get(c['f'])
        if c_val is not None and len(c_val):
            c_val = c_val.replace('*', '%')  # Treat input '*' as % for like statement
            isNot = False
            isNull = False
            if c_val[0] == '!':  # If starting with an !, use not like
                isNot = True
                c_val = c_val[1:]
                if not len(c_val): # not nothing is null
                    isNot = False
                    isNull = True
                elif c_val[0] == '!':  # If starting with an !! is for not null
                    c_val = c_val[1:]
                    isNull = True

            if c['t'] == bool:
                kwargs = {
                    c['f']: c_val.upper().startswith('T'),
                }
            elif isNull:
                kwargs = {
                    '{0}__isnull'.format(c['f']): True,
                }
            elif c['t'] == str:
                if len(c_val):
                    if c_val[0] == '^':  # Add wild card to start unless anchored with ^
                        c_val = c_val[1:]
                        if not len(c_val):
                            continue
                    else:
                        c_val = '%' + c_val
                    if c_val[-1] == '$':  # Add wild card to end unless anchored with $
                        c_val = c_val[:-1]
                        if not len(c_val):
                            continue
                    else:
                        c_val = c_val + '%'

                kwargs = {
                    c['e']: c_val,
                }
            else:  # pragma: no cover currently not tested, in case of introduction of new data type ie date/int, it will be applicable
                kwargs = {
                    c['e']: c_val,
                }
            if isNot:
                queryset = queryset.exclude(**kwargs)
            else:
                queryset = queryset.filter(**kwargs)

    # If orderBy is in the request, it takes precedence over the default
    # Keep the default order at the end, to assure unique ordering
    o = request_GET.get('orderBy')
    if o and len(o):
        orderBy = list(filter(lambda x: (x != o), orderBy))
        orderBy = [o] + orderBy
    queryset = queryset.order_by(*orderBy)

    return queryset