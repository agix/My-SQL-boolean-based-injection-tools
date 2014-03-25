Usage: mysql-truefalse.py [options]

Options:
  -h, --help            show this help message and exit
  -u URL, --url=URL     url where sql injection was found with 1=.?1 where
                        injection is
  -d DATABASE, --database=DATABASE
                        Dump table from database
  -t TABLE, --table=TABLE
                        Dump colonne from table and database
  -c COLONNE, --colonne=COLONNE
                        Dump result from column, table and database
  -f FILE, --file=FILE  Try to dump load_file()
  -S SPECIAL, --Special=SPECIAL
                        dump special function (@@version...)
  -p POST, --post=POST  Add post data with 1=.?1 where injection is
  -s COOKIE, --session=COOKIE
                        Add cookie data with 1=.?1 where injection is
  -E ERROR, --Error=ERROR
                        If hard to determine good page, give some strings in
                        1=2 page
  -v, --verbose         Print url request
  -b BEGIN, --begin=BEGIN
                        Start dumping with the <begin> line
  -e END, --end=END     Finish dumping with the <end> line
  -C CONDITION, --Condition=CONDITION
                        Specify condition ex : -C 'login=admin'
  -m MODIFICATION, --Modif=MODIFICATION
                        Specify tricks to bypass filter (type -m list to list
                        the tricks)
