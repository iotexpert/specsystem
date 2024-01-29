import re
from utils.dev_utils import formatError
from django.db import connection
from django.db.models.query import RawQuerySet
from rest_framework.pagination import LimitOffsetPagination

class RawSQLQuerySet(RawQuerySet):
    """ Building a Raw query

        col_exp: The cluase the select is returning
        from_exp: The from clause
        filter_conditions: (optional) filters that are not: <col> like ''
        orderby_exp: (optional) Default sort order
    """
    col_exp = None
    from_exp = None
    filter_conditions = {}
    filter_exp = None
    orderby_exp = None

    offset = 0
    limit = 100
    data = []

    def __init__(self, col_exp, from_exp, reqDict, filter_conditions=None, orderby_exp=None):
        self.col_exp = col_exp
        self.filter_conditions = filter_conditions
        self.from_exp = from_exp
        super().__init__(self.raw_sql())

        self.offset = reqDict.get('offset', 0)
        self.limit = reqDict.get('limit', self.limit)

        # Build filterable column list
        col_exp_split = col_exp.split(',\n')
        col_exp_split = [str(c).strip(' \t\n\r').split(' ') for c in col_exp_split]
        cols = {c[-1]: " ".join(c[0:-1]) for c in col_exp_split if len(c) >= 2}
        for c in cols:
            # setdefault used to avoid overwriting any passed in filter_conditions
            self.filter_conditions.setdefault(c, cols[c] + " like '{s}' ")
            self.filter_conditions.setdefault('null '+c, "("+cols[c] +" is null or " + cols[c] + " ='' )")

        # Build filter list
        filter_arr = ["where 1=1"]
        for k in reqDict:
            if k in self.filter_conditions:
                parm = reqDict[k]
                if not len(parm):
                    continue
                # if an array is passed in, use an 'in' clause
                if isinstance(parm, list):
                        filter_arr.append(k+' in (' + ','.join("'"+p+"'" for p in parm)+')')
                        continue
                parm = parm.replace('*', '%')  # Treat input '*' as % for like statement
                isNot = False
                if parm[0] == '!':  # If starting with an !, use not like
                    isNot = True
                    parm = parm[1:]
                    if not len(parm): # if a bare !, then not null
                        filter_arr.append('not ' + self.filter_conditions['null '+k])
                        continue
                if parm[0] == '!':  # If starting with an !! is used to find null
                    filter_arr.append(self.filter_conditions['null '+k])
                    continue
                if parm[0] == '^':  # Add wild card to start unless anchored with ^
                    parm = parm[1:]
                    if not len(parm):
                        continue
                else:
                    parm = '%' + parm
                if parm[-1] == '$':  # Add wild card to end unless anchored with $
                    parm = parm[:-1]
                    if not len(parm):
                        continue
                else:
                    parm = parm + '%'

                parm =re.sub("[^-_ %A-Z0-9]", "", parm,0,re.IGNORECASE) # remove quotes and other unknowns
                f = self.filter_conditions[k].format(s=parm)
                filter_arr.append(('not ' if isNot else '') + f)

        self.filter_exp = " and ".join(filter_arr)

        # Set the order by
        orderby_val = reqDict.get('orderBy', orderby_exp)
        orderby_dir = 'desc' if orderby_val.startswith('-') else 'asc'
        orderby_val = orderby_val.removeprefix('-')

        # If the order by is invalid, just ignore it and go with the default
        if orderby_val not in cols:
            orderby_val = orderby_exp
            orderby_dir = 'desc' if orderby_val.startswith('-') else 'asc'
            orderby_val = orderby_val.removeprefix('-')
        self.orderby_exp = f"order by {cols[orderby_val]} {orderby_dir}"

    def count(self):
        try:
            with connection.cursor() as cursor:
                cursor.execute(f"select count(*) {self.from_exp} {self.filter_exp}")

                return cursor.fetchall()[0][0]
        except BaseException as be: # pragma: no cover
            formatError(be, "SQL-001")

    def raw_sql(self):
        return f"select {self.col_exp} {self.from_exp} {self.filter_exp} {self.orderby_exp}"

    def get_data(self):
        try:
            with connection.cursor() as cursor:
                sql = self.raw_sql() + f' offset {self.offset} rows fetch next {self.limit} rows only'
                cursor.execute(sql)

                columns = [column[0] for column in cursor.description]

                self.data = []
                for row in cursor.fetchall():
                    self.data.append(dict(zip(columns, row)))
                return self.data
        except BaseException as be: # pragma: no cover
            formatError(be, "SQL-002")

    def get_all_data(self):
        self.offset = 0
        self.limit = 1000000 # cap at some high level to prevent too big of data sets
        return self.get_data()

class RawSQLPagination(LimitOffsetPagination):
    def paginate_queryset(self, queryset, request, view=None):
        self.limit = self.get_limit(request)
        if self.limit is None:  # pragma: no cover
            return None

        self.count = self.get_count(queryset)
        self.offset = self.get_offset(request)
        self.request = request
        if self.count > self.limit and self.template is not None:
            self.display_page_controls = True

        if self.count == 0 or self.offset > self.count:
            return []
        return queryset.get_data()
