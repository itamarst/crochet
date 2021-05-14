try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

import versioneer


def read(path):
    """
    Read the contents of a file.
    """
    with open(path, encoding="utf-8") as f:
        return f.read()


setup(
    classifiers=[
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: Implementation :: CPython',
        'Programming Language :: Python :: Implementation :: PyPy',
    ],
    name='crochet',
    version=versioneer.get_version(),
    cmdclass=versioneer.get_cmdclass(),
    description="Use Twisted anywhere!",
    python_requires=">=3.6.0",
    install_requires=[
        "Twisted>=16.0",
        "wrapt",
    ],
    keywords="twisted threading",
    license="MIT",
    package_data={"crochet": ["py.typed", "*.pyi"]},
    packages=["crochet", "crochet.tests"],
    url="https://github.com/itamarst/crochet",
    maintainer='Itamar Turner-Trauring',
    maintainer_email='itamar@itamarst.org',
    long_description=read('README.rst') + '\n' + read('docs/news.rst'),
)
