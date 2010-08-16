from textwrap import dedent
from setuptools import setup

setup(
        name = "lojbansuggest",
        version = "0.2.2",
        author = "Timo Paulssen",
        author_email = "timo+lojbansuggest@wakelift.de",
        download_url = "http://wakelift.de/lojban/software/python/lojbansuggest-0.2.2.tar.gz",
        license = "BSD",
        install_requires = ["lojbantools"],
        scripts = ["scripts/%s" % filename for filename in ["suggest.py",
                   "showlojbantree.sh",
                   "lojbantreeproj.py"]],
        packages = ["lojbansuggest"],
        dependency_links = ["http://wakelift.de/lojban/software/"],
        
        classifiers = ["Development Status :: 3 - Alpha",
            "Environment :: Console",
            "Intended Audience :: Education",
            "Intended Audience :: Developers",
            "License :: OSI Approved :: BSD License",
            "Operating System :: OS Independent",
            "Programming Language :: Python",
            "Topic :: Text Processing :: Linguistic",
        ],
        long_description = dedent("""\
            =============
            Lojbansuggest
            =============

            This library is made up of two independent parts:

            suggest
            -------

            This is a library and a thin commandline that takes a lojban sentence and looks for common beginner mistakes and makes suggestions for corrections.

            tree
            ----

            This is a library to turn a lojban sentence into an approximate analysis of the semantics (for example what sumti goes into what place of what tanru unit).

            At the moment it's not very powerful.""")


)
