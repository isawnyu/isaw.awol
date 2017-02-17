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

## Other utilities and scripts

### ```bin/walk_for_keywords.py```

```
$ python bin/walk_for_keywords.py -h
usage: walk_for_keywords.py [-h] [-l LOGLEVEL] [-v] [-vv] [--progress] whence

Script to walk AWOL backup and look for new keywords.

positional arguments:
  whence                path to directory to read and process

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

Running this script on a new blog backup will identify and print out new keywords (and typos) found in the categories assigned to blog posts. These  need to be added to the ```isaw/awol/awol_title_strings.csv``` file in order to get ```walk_to_json.py``` to run clean. This CSV file is used by that script for keyword authority control and for mining keyword associations out of titles and other content. A good way to get clean output is to run it like:

```python bin/walk_for_keywords.py --loglevel CRITICAL /path/to/awol-content/posts```

## Classes

The following classes are defined:

### AwolArticle: ```isaw/awol/awol_article.py```

Extracts, normalizes, and stores data from an AWOL blog post.

### Resource: ```isaw/awol/resource.py```

Store, manipulate, and export data about a single information resource.

### AwolParsers: ```isaw/awol/parse/awol_parsers.py```

Pluggable framework for parsing content from an AwolArticle. 

### AwolBaseParser ```isaw/awol/parse/awol_parse.py```

Base class for parsers that extract resource data from an AwolArticle. 

Two subclasses that inherit from base class are used directly in code:

#### awol_parse_generic.Parser: ```isaw/awol/parse/awol_parse_generic.py```

Extract data from an AWOL blog post agnostic to domain of resource.

#### awol_parse_generic_single.Parser: ```isaw/awol/parse/awol_parse_generic_single.py```

Extract data from an AWOL blog post on the assumption the post is about a single resource.

### AwolDomainParser: ```isaw/awol/parse/awol_parse_domain.py```

Inherits from the AwolBaseParser, providing a specialized superclass on which to construct parsers that require specific parsing/extraction behaviors for resources from one particular domain. Such parsers may be created by inheritance from this class and selective override of methods. These are packaged one to a module and saved in ```isaw/awol/parse/``` with filenames that contain the string 'parse'. See, for example:

#### awol_parse_ascsa.Parser: ```isaw/awol/parse/awol_parse_ascsa.py```

Extract data from an AWOL blog post that contains information about resources in the domain ```www.ascsa.edu.gr```.

## Etc.

Includes: http://code.activestate.com/recipes/579018-python-determine-name-and-directory-of-the-top-lev/

