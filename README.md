# PySpark Style Guide

![Github](https://img.shields.io/badge/code%20style-black-000000.svg)
![GitHub](https://img.shields.io/github/license/vectra-ai-research/pyspark-style-guide)

The purpose of this document is to help teams write readable and maintainable programs using [Apache PySpark](https://spark.apache.org/docs/latest/api/python/). This style guide is designed to complement [Black's](https://github.com/psf/black) automatic formatting of Python code. For each style choice, we provide an example and the reasoning behind it. We hope they will make it easier to write high quality PySpark code. 

This document is an evolving guide. We encourage your suggestions, additions, or improvements (see our section on [contributing](#contributing)).

## Table of Contents
- [PySpark Style Guide](#pyspark-style-guide)
  - [Table of Contents](#table-of-contents)
  - [Guide](#guide)
    - [Import pyspark functions, types, and window narrowly and with consistent aliases](#import-pyspark-functions-types-and-window-narrowly-and-with-consistent-aliases)
    - [When equivalent functions are available use a common set](#when-equivalent-functions-are-available-use-a-common-set)
    - [Use column name strings to access columns](#use-column-name-strings-to-access-columns)
    - [When a function accepts a column or column name, use the column name option](#when-a-function-accepts-a-column-or-column-name-use-the-column-name-option)
    - [When a function accepts unlimited arguments, avoid passing a list](#when-a-function-accepts-unlimited-arguments-avoid-passing-a-list)
    - [Factor out common logic](#factor-out-common-logic)
    - [When the output of a function is stored as a column, give the column a concise name](#when-the-output-of-a-function-is-stored-as-a-column-give-the-column-a-concise-name)
    - [When chaining several functions, open a cleanly indentable block using parentheses](#when-chaining-several-functions-open-a-cleanly-indentable-block-using-parentheses)
    - [Try to break the query into reasonably sized named chunks](#try-to-break-the-query-into-reasonably-sized-named-chunks)
    - [Use descriptive names for dataframes](#use-descriptive-names-for-dataframes)
    - [Group related filters, keep unrelated filters as serial `filter` calls](#group-related-filters-keep-unrelated-filters-as-serial-filter-calls)
    - [Prefer use of window functions to equivalent re-joining operations](#prefer-use-of-window-functions-to-equivalent-re-joining-operations)
  - [Contributing](#contributing)


## Guide
### Import pyspark functions, types, and window narrowly and with consistent aliases
```python
# good
from pyspark.sql import functions as F
from pyspark.sql import types as T
from pyspark.sql import window as W
from pyspark.sql import SparkSession, DataFrame

# bad
from pyspark import *

# bad
from pyspark.sql.functions import *
```
This prevents name collisions, as many PySpark functions have common names. This will make our code more consistent.


### When equivalent functions are available use a common set
| Preferred         | Alternate        | Reason                                  |
| ----------------- | ---------------- | --------------------------------------- |
| `where`           | `filter`         | Less ambiguous and more similar to SQL  |
| `groupby`         | `groupBy`        | More consistent with Python conventions |
| `drop_duplicates` | `dropDuplicates` | More consistent with Python conventions |
| `astype`          | `cast`           | Arbitrary                               |
| `alias`           | `name`           | More specific                           |
| `mean`            | `avg`            | More specific                           |
| `stddev`          | `stddev_sample`  | More concise                            |
| `var`             | `var_sample`     | More concise                            |
```python
# good
df.where(my_filter)

# bad  
df.filter(my_filter) 
```
These (somewhat arbitrary) choices will make our code more consistent.


### Use column name strings to access columns
```python
# good
F.col("col_name")

# bad
df.col_name
```
Using the dot notation presents several problems. It can lead to name collisions if a column shares a name with a dataframe method. It requires the version of the dataframe with the column you want to access to be bound to a variable, but it may not be. It also doesn't work if the column name contains certain non-letter characters. The most obvious exception to this are joins where the joining column has a different name in the two tables.
```python
downloads.join(
  users, 
  downloads.user_id == user.id,
)
```

### When a function accepts a column or column name, use the column name option
```python
# good
F.collect_set("client_ip")

# bad
F.collect_set(F.col("client_ip"))
```
Expressions are easier to read without the extra noise of `F.col()`.


### When a function accepts unlimited arguments, avoid passing a list
```python
# good
groupby("user_id", "operation")

# bad
groupby([F.col("user_id"), F.col("operation")])
```
Expressions are easier to read without the extra noise.


### Factor out common logic
```python
# good
DOWNLOADED_TODAY = (F.col("operation") == "Download") & F.col("today")
csv_downloads_today = df.where(DOWNLOADED_TODAY & (F.col("file_extension") == "csv"))
exe_downloads_today = df.where(DOWNLOADED_TODAY & (F.col("file_extension") == "exe"))

# bad
csv_downloads_today = df.where(
    (F.col("operation") == "Download") & F.col("today") & (F.col("file_extension") == "csv")
)
exe_downloads_today = df.where(
    (F.col("operation") == "Download") & F.col("today") & (F.col("file_extension") == "exe")
)
```
It is okay to reuse these variables even though they include calls to `F.col`. This prevents repeated code and can make code easier to read.


### When the output of a function is stored as a column, give the column a concise name
```python
# good
result = logs.groupby("user_id").agg(
    F.count("operation").alias("operation_count"),
)
result.printSchema()

# root
# |-- user_id: string
# |-- operation_count: long


# bad
result = logs.groupby("user_id").agg(
    F.count("operation"),
)
result.printSchema()

# root
#  |-- user_id: string
#  |-- count(operation): long
```
The default column names are usually awkward, probably defy the naming style of other columns, and can get long.


### When chaining several functions, open a cleanly indentable block using parentheses
```python
# good
result = (
    df
    .groupby("user_id", "operation")
    .agg(
        F.min("creation_time").alias("start_time"),
        F.max("creation_time").alias("end_time"),
        F.collect_set("client_ip").alias("ips")
    )
)

# bad
result = df.groupby("user_id", "operation").agg(
        F.min("creation_time").alias("start_time"),
        F.max("creation_time").alias("end_time"),
        F.collect_set("client_ip").alias("ips"),
)
```


### Try to break the query into reasonably sized named chunks
```python
# good
downloading_users = logs.where(F.col("operation") == "Download").select("user_id").distinct()

downloading_user_operations = (
    logs.join(downloading_users, "user_id")
    .groupby("user_id")
    .agg(
        F.collect_set("operation").alias("operations_used"),
        F.count("operation").alias("operation_count"),
    )
)

# bad (logical chunk not broken out)
downloading_user_operations = (
    logs.join(
        (logs.where(F.col("operation") == "Download").select("user_id").distinct()), "user_id"
    )
    .groupby("user_id")
    .agg(
        F.collect_set("operation").alias("operations_used"),
        F.count("operation").alias("operation_count"),
    )
)

# bad (chunks too small)
download_logs = logs.where(F.col("operation") == "Download")

downloading_users = download_logs.select("user_id").distinct()

downloading_user_logs = logs.join(downloading_users, "user_id")

downloading_user_operations = downloading_user_logs.groupby("user_id").agg(
    F.collect_set("operation").alias("operations_used"),
    F.count("operation").alias("operation_count"),
)
```
Choosing when and what to name variables is always a challenge. Resisting the urge to create long PySpark function chains makes the code more readable.


### Use descriptive names for dataframes
```python
# good
def get_large_downloads(downloads):
    return downloads.where(F.col("size") > 100)


# bad
def get_large_downloads(df):
    return df.where(F.col("size") > 100)
```
Good naming is common practice for normal Python functions, but many PySpark examples found online refer to tables as just `df`. Finding appropriate names for dataframes makes code easier to understand quickly.


### Group related filters, keep unrelated filters as serial `filter` calls
```python
# good
result = (
    downloads.where((F.col("time") >= yesterday) & (F.col("time") < now))
    .where(F.col("size") > 100)
    .where(F.col("user_id").isNotNull())
)

# bad
result = (
    downloads.where((F.col("time") >= yesterday) & (F.col("time") < now))
    & (F.col("size") > 100)
    & F.col("user_id").isNotNull()
)
# bad
result = (
    downloads.where(F.col("time") >= yesterday)
    .where(F.col("time") < now)
    .where(F.col("size") > 100)
    .where(F.col("user_id").isNotNull())
)

```
Filters like this are automatically combined during Spark's optimization, so this is purely a matter of style. Keeping this distinction makes filters easier to read.


### Prefer use of window functions to equivalent re-joining operations
```python
# good
window = W.Window.partitionBy(F.col("user_id"))
result = downloads.withColumn("download_count", F.count("*").over(window))

# bad
result = downloads.join(
    downloads.groupby("user_id").agg(F.count("*").alias("download_count")), "user_id"
)
```
The window function version is usually easier to get right and is usually more concise.


### Create multiple new columns using `select` instead of `withColumn`
```python
previous_domains = F.coalesce("previous_domains", F.array([]))

# Option A: good
df.select(
    "ip",
    "domains",
    previous_domains.alias("previous_domains"),
    F.array_except("domains", previous_domains).alias("new_domains"),
    F.col("user_id").alias("user_name")
)

# Option B: bad - the old previous_domains column is used to create new_domains (may result in unwanted null values)
df.select(
    "ip",
    "domains",
    F.coalesce("previous_domains", F.array([])).alias("previous_domains"),
    F.array_except("domains", "previous_domains").alias("new_domains"),
    F.col("user_id").alias("user_name")
)

# Option C: bad - not explicit, may result in duplicate column names
df.select(
    "*",
    previous_domains.alias("previous_domains"),
    F.array_except("domains", previous_domains).alias("new_domains"),
    F.col("user_id").alias("user_name"),
)

# Option D: bad - involves an additional Project stage
df.withColumn(
    "previous_domains", F.coalesce("previous_domains", F.array([]))
).withColumn(
    "new_domains", F.array_except("domains", "previous_domains")
).withColumnRenamed(
    "user_id", "user_name"
)
```
In addition to improved readability, using `select` to create new columns provides an additional advantage: it ensures that all of the columns are created in only one `Project` stage, whereas 
`withColumn` creates additional internal projection stages (see the [PySpark documentation](https://spark.apache.org/docs/latest/api/python/reference/api/pyspark.sql.DataFrame.withColumn.html)). Using a single `select` statement simplifies the physical plan and will likely improve query performance.

Here is how the physical plan differs for the examples above:
- Option A
```
== Physical Plan ==
*(1) Project [ip#10149, domains#10148, coalesce(previous_domains#10150, []) AS previous_domains#10194, array_except(domains#10148, coalesce(previous_domains#10150, [])) AS new_domains#10195, user_id#10151 AS user_name#10196]
+- *(1) Scan ExistingRDD[domains#10148,ip#10149,previous_domains#10150,user_id#10151]
```
- Option B - `previous_domains#10150` efers to the original column (not coalesced with `[]`)
```
== Physical Plan ==
*(1) Project [ip#10149, domains#10148, coalesce(previous_domains#10150, []) AS previous_domains#10202, array_except(domains#10148, previous_domains#10150) AS new_domains#10203, user_id#10151 AS user_name#10204]
+- *(1) Scan ExistingRDD[domains#10148,ip#10149,previous_domains#10150,user_id#10151]
```
- Option C - unwanted or duplicate columns
```
== Physical Plan ==
*(1) Project [domains#10148, ip#10149, previous_domains#10150, user_id#10151, coalesce(previous_domains#10150, []) AS previous_domains#10210, array_except(domains#10148, coalesce(previous_domains#10150, [])) AS new_domains#10211, user_id#10151 AS user_name#10212]
+- *(1) Scan ExistingRDD[domains#10148,ip#10149,previous_domains#10150,user_id#10151]
```
- Option D - additional Project stage
```
== Physical Plan ==
*(1) Project [domains#10148, ip#10149, previous_domains#10220, user_id#10151 AS user_name#10231, array_except(domains#10148, previous_domains#10220) AS new_domains#10225]
+- *(1) Project [domains#10148, ip#10149, coalesce(previous_domains#10150, []) AS previous_domains#10220, user_id#10151]
   +- *(1) Scan ExistingRDD[domains#10148,ip#10149,previous_domains#10150,user_id#10151]
```

## Contributing
One of the main purposes of this document is to encourage consistency. Some choices made here are arbitrary, but we hope they will lead to more readable code. Other choices may prove wrong with more time and experience. Suggestions for changes to the guide or additions to it are welcome. Please feel free to create an issue or pull request to start a discussion.
