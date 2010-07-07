from setuptools import setup

setup(
        name = "lojbansuggest",
        version = "0.2.1",
        author = "Timo Paulssen",
        author_email = "timo+lojbansuggest@wakelift.de",
        download_url = "http://wakelift.de/lojban/software/python/lojbansuggest-0.2.1.tar.gz",
        license = "BSD",
        install_requires = ["lojbantools"],
        scripts = ["suggest.py",
                   "showlojbantree.sh",
                   "lojbantreeproj.py"],
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
)
