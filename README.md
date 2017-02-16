#isaw.awol

The Ancient World Online: from blog to bibliographic data.

Uses python 2.7. For dependencies, see REQUIREMENTS.txt. There are nosetests in isaw/awol/tests.

## Usage

You need the AWOL blog backup split up as found in https://github.com/isawnyu/awol-content.

```
$ python bin/walk_to_json.py -h
usage: walk_to_json.py [-h] [-l LOGLEVEL] [-v] [-vv] [--progress]
                       whence thence

Script to walk AWOL backup and create json resource files.

positional arguments:
  whence                path to directory to read and process
  thence                path to directory where you want the json-serialized
                        resources dumped

optional arguments:
  -h, --help            show this help message and exit
  -l LOGLEVEL, --loglevel LOGLEVEL
                        desired logging level (case-insensitive string: DEBUG,
                        INFO, WARNING, ERROR (default: None)
  -v, --verbose         verbose output (logging level == INFO (default: False)
  -vv, --veryverbose    very verbose output (logging level == DEBUG (default:
                        False)
  --progress            show progress (default: False)
```

I.e., try something like:

> python bin/walk_to_json.py --progress /path/to/awol-content/posts /path/to/somewhere/else/

## Interesting classes

The following classes are defined:

### AwolArticle: ```isaw/awol/awol_article.py```

Extracts, normalizes, and stores data from an AWOL blog post.

### Resource: ```isaw/awol/resource.py```

Store, manipulate, and export data about a single information resource.

### AwolParsers: ```isaw/awol/parse/awol_parsers.py```

Pluggable framework for parsing content from an AwolArticle.

### AwolBaseParser

Superclass to extract resource data from an AwolArticle. Other parsers are built on this extensive base by inheriting it and selectively overriding its methods.

Includes: http://code.activestate.com/recipes/579018-python-determine-name-and-directory-of-the-top-lev/

