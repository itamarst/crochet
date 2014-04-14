import os

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup


def get_crochet_version():
    """
    Get crochet version from version module without importing more than
    necessary.
    """
    this_dir_path = os.path.dirname(__file__)
    crochet_module_path = os.path.join(this_dir_path, "crochet")
    version_module_path = os.path.join(crochet_module_path, "_version.py")

    # The version module contains a variable called __version__
    with open(version_module_path) as version_module:
        exec(version_module.read())
    return locals()["__version__"]

def read(path):
    """
    Read the contents of a file.
    """
    with open(path) as f:
        return f.read()

setup(
    classifiers=[
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: Implementation :: CPython',
        'Programming Language :: Python :: Implementation :: PyPy',
    ],
    name='crochet',
    version=get_crochet_version(),
    description="Use Twisted anywhere!",
    install_requires=[
        "Twisted>=11.1",
    ],
    keywords="twisted threading",
    license="MIT",
    packages=["crochet", "crochet.tests"],
    url="https://github.com/itamarst/crochet",
    maintainer='Itamar Turner-Trauring',
    maintainer_email='itamar@itamarst.org',
    long_description=read('README.rst') + '\n' + read('docs/news.rst'),
)
