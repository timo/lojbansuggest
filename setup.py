from setuptools import setup

setup(
        name = "lojbansuggest",
        version = "0.2",
        author = "Timo Paulssen",
        author_email = "timo+lojbansuggest@wakelift.de",
        download_url = "http://wakelift.de/lojban/software/python/lojbansuggest-0.2.tar.gz",
        install_requires = ["lojbantools"],
        scripts = ["suggest.py",
                   "showlojbantree.sh",
                   "lojbantreeproj.py"],
        packages = ["lojbansuggest"],
        dependency_links = ["http://wakelift.de/lojban/software/python/lojbantools-0.2.tar.gz"],

)
